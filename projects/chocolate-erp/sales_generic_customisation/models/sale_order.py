from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tools import format_date, frozendict
from odoo.tools import float_compare

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_type = fields.Selection([
        ('wholesale', 'Wholesale'),
        ('b2b', 'B2B'),
        ('vansale', 'Van Sale')
    ], string="Sales Type")

    has_price_alert = fields.Boolean(
        string="Has Price Alert",
        compute='_compute_has_price_alert',
        store=True
    )
    total_discount = fields.Monetary(string='Discount Amount', compute='_compute_discount_amount', store=True, readonly=True)
    promotional_sale = fields.Boolean(string='Promotional Sale', default=False)

    @api.depends('order_line.discount_amount')
    def _compute_discount_amount(self):
        for order in self:
            order.total_discount = sum(order.order_line.mapped('discount_amount'))

    @api.depends('order_line.price_unit', 'order_line.purchase_price', 'order_line.product_id.is_storable')
    def _compute_has_price_alert(self):
        for order in self:
            order.has_price_alert = any(
                line.purchase_price > line.price_unit and line.product_id.is_storable
                for line in order.order_line
            )
    
    def _compute_tax_totals(self):
        res = super(SaleOrder, self)._compute_tax_totals()
        AccountTax = self.env['account.tax']
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.is_discount and not x.is_round_off)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )
            if order.total_discount > 0:
                order.tax_totals['discount'] = order.total_discount
            global_discount = sum(order.order_line.filtered(lambda x: x.is_discount == True).mapped('price_subtotal'))
            round_off = sum(order.order_line.filtered(lambda x: x.is_round_off == True).mapped('price_subtotal'))
            if round_off:
                order.tax_totals['round_off'] = round_off
            order.tax_totals['total_amount_currency'] = order.tax_totals['total_amount_currency'] + global_discount + round_off
            # Change untaxed amount to taxable
            if 'subtotals' in order.tax_totals:
                for subtotal in order.tax_totals['subtotals']:
                    if subtotal.get('name') == 'Untaxed Amount':
                        subtotal['name'] = 'Taxable'
        return res
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        for order in self:
            for move in moves:
                move.sale_type = order.sale_type
            # For promotional sale, create a journal entry for the promotional expense
            if order.promotional_sale:
                if not order.company_id.promotional_expense_account_id:
                    raise UserError(_("Please set a default promotional expense account for the company."))
                for invoice_line in moves.invoice_line_ids:
                    invoice_line.account_id = order.company_id.promotional_expense_account_id
                
        return moves
    
    @api.constrains('order_line')
    def check_order_line_price(self):
        for order in self:
            if any(line.price_unit <= 0 for line in order.order_line.filtered(lambda x: not x.is_discount and not x.is_round_off)) and not order.promotional_sale:
                raise UserError("The price of a product on a sale order line cannot be zero or less. Please set a valid price for the product.")
            

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    expiration_date = fields.Datetime(related='lot_id.expiration_date', string="Lot Expiry", store=True)
    internal_reference = fields.Char(
        string='Internal Reference',
        related='product_id.default_code',
        store=True,
        readonly=True,
    )
    is_discount = fields.Boolean(string='Is Discount', default=False)
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount_amount', store=True)
    offer_id = fields.Many2one('product.offer',string='Offer')
    product_uom = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        domain="product_uom_domain")
    product_uom_domain = fields.Binary(string='Product UoM Domain', compute='_compute_product_uom_domain')

    @api.depends('product_id')
    def _compute_product_uom_domain(self):
        for line in self:
            uom_ids = [line.product_id.uom_id.id]
            if line.product_id.product_uom_ids:
                uom_ids += line.product_id.product_uom_ids.ids
            else:
                uom_ids += line.product_id.uom_id.category_id.uom_ids.ids
            line.product_uom_domain = [('id', 'in', uom_ids)]

    @api.depends('product_uom_qty', 'price_unit', 'price_subtotal')
    def _compute_discount_amount(self):
        for line in self:
            line.discount_amount = (line.product_uom_qty * line.price_unit) - line.price_subtotal
            if line.is_discount:
                line.discount_amount = -1 * line.price_subtotal

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields generated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or line.order_id.locked or line.product_id.type != 'consu':
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            origin = f'{line.order_id.name} - {line.order_id.client_order_ref}' if line.order_id.client_order_ref else line.order_id.name
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, line_uom)
            procurements += line._create_procurements(product_qty, procurement_uom, origin, values)
        if procurements:
            self.env['procurement.group'].run(procurements)

        # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
        return True
    
    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            "is_discount": self.is_discount,
            "lot_id": self.lot_id.id,
            "expiration_date": self.expiration_date,
            "purchase_price": self.purchase_price
            })
        return res


    @api.depends('move_ids', 'move_ids.stock_valuation_layer_ids', 'move_ids.picking_id.state')
    def _compute_purchase_price(self):
        line_ids_to_pass = set()
        for line in self:
            product = line.product_id.with_company(line.company_id)
            if not line.has_valued_move_ids():
                line_ids_to_pass.add(line.id)
            elif (
                # don't overwrite any existing value unless non-standard cost method
                (line.product_id and line.product_id.categ_id.property_cost_method != 'standard') or
                # if line added from delivery, allow recomputation
                (not line.product_uom_qty and line.qty_delivered)
            ):
                purch_price = product._compute_average_price(0, line.product_uom_qty or line.qty_to_invoice, line.move_ids)
                if line.lot_id and line.lot_id.is_branch_sale:
                    purch_price = product.uom_id._compute_price(
                        line.lot_id.with_company(line.company_id).standard_price + line.lot_id.margin,
                        line.product_uom
                    )
                if line.product_uom != product.uom_id:
                    purch_price = product.uom_id._compute_price(purch_price, line.product_uom)
                line.purchase_price = line._convert_to_sol_currency(
                    purch_price,
                    product.cost_currency_id,
                )
        return super(SaleOrderLine, self.browse(line_ids_to_pass))._compute_purchase_price()