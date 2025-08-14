from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PurchaseReturn(models.Model):
    _name = 'purchase.return'
    _description = 'Purchase Return'


    name = fields.Char(string='Name', readonly=True, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Supplier')
    purchase_ids = fields.Many2many('purchase.order', string='Purchase Order')
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bills')
    return_date = fields.Datetime(string='Return Date', default=fields.Datetime.now)
    return_line_ids = fields.One2many('purchase.return.line', 'return_id', string='Return Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, default='draft')
    return_reason = fields.Text(string='Return Reason')
    return_picking_id = fields.Many2one('stock.picking', string='Return Picking', copy=False)
    location_id = fields.Many2one('stock.location', string='Location', domain=[('usage', '=', 'internal')], default=lambda self: self._get_default_location())
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    picking_count = fields.Integer(compute='_compute_picking_count', string='Picking Count')
    refund_count = fields.Integer(compute='_compute_refund_count', string='Refund Count')
    picking_ids = fields.One2many("stock.picking", "purchase_return_id", string="Return Stock Delivery")
    bill_refund_ids = fields.One2many("account.move", "purchase_return_id", string="Bill Refunds")
    amount_untaxed = fields.Monetary(string='Taxable', store=True, readonly=True, compute='_amount_all', tracking=True)
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)
    amount_tax = fields.Monetary(string='Vat', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    total_discount = fields.Monetary(string='Discount Amount', compute='_compute_discount_amount', store=True, readonly=True)

    @api.depends('return_line_ids.price_subtotal', 'company_id')
    def _amount_all(self):
        AccountTax = self.env['account.tax']
        for p_return in self:
            p_return_lines = p_return.return_line_ids
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in p_return_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, p_return.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, p_return.company_id)
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=p_return.currency_id or p_return.company_id.currency_id,
                company=p_return.company_id,
            )
            p_return.amount_untaxed = tax_totals['base_amount_currency']
            p_return.amount_tax = tax_totals['tax_amount_currency']
            p_return.amount_total = tax_totals['total_amount_currency']

    @api.depends('return_line_ids.price_subtotal', 'currency_id', 'company_id')
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']
        for p_return in self:
            if not p_return.company_id:
                p_return.tax_totals = False
                continue
            p_return_lines = p_return.return_line_ids.filtered(lambda x: not x.is_roundoff)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in p_return_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, p_return.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, p_return.company_id)
            p_return.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=p_return.currency_id or p_return.company_id.currency_id,
                company=p_return.company_id,
            )
            if p_return.total_discount > 0:
                p_return.tax_totals['discount'] = p_return.total_discount
            round_off = sum(p_return.return_line_ids.filtered(lambda x: x.is_roundoff == True).mapped('price_subtotal'))
            if round_off:
                p_return.tax_totals['round_off'] = round_off
            p_return.tax_totals['total_amount_currency'] = p_return.tax_totals['total_amount_currency'] + round_off
            if 'subtotals' in p_return.tax_totals:
                for subtotal in p_return.tax_totals['subtotals']:
                    if subtotal.get('name') == 'Untaxed Amount':
                        subtotal['name'] = 'Taxable'

    @api.depends('return_line_ids.discount_amount')
    def _compute_discount_amount(self):
        for p_return in self:
            p_return.total_discount = sum(p_return.return_line_ids.mapped('discount_amount'))

    def _get_default_location(self):
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company.id)], limit=1)
        return warehouse.lot_stock_id if warehouse else False

    @api.onchange('vendor_bill_id')
    def _onchange_vendor_bill_id(self):
        if self.vendor_bill_id:
            purchase = self.env['purchase.order'].search([('invoice_ids', 'in', self.vendor_bill_id.ids)])
            self.purchase_ids = [(6, 0, purchase.ids)]

    @api.onchange('purchase_ids')
    def purchase_ids_onchange_(self):
        self.return_line_ids = False
        lines = []
        for purchase in self.purchase_ids:
            for line in purchase.order_line.move_ids.move_line_ids.filtered(lambda x: x.state == 'done' and x.location_id.id == purchase.picking_type_id.default_location_src_id.id):
                lines.append((0, 0, {
                    'purchase_line_id': line.move_id.purchase_line_id.id,
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'uom_id': line.move_id.purchase_line_id.product_uom.id,
                    'price_unit': line.move_id.purchase_line_id.price_unit,
                    'lot_id': line.lot_id.id if line.lot_id else False,
                    'move_id': line.move_id.id,
                    'tax_ids': [(6, 0, line.move_id.purchase_line_id.taxes_id.ids)],
                    'discount': line.move_id.purchase_line_id.discount,
                    'discount_fixed': line.move_id.purchase_line_id.discount_fixed,

                }))
        self.return_line_ids = lines

    def action_confirm(self):
        self.check_product_availabilty()
        for line in self.return_line_ids:
            if line.return_qty == 0:
                line.unlink()
        self.write({'state': 'confirmed'})

    def check_product_availabilty(self):
        for line in self.return_line_ids.filtered(lambda x: not x.is_roundoff):
            free_qty = line.product_id.with_context(location=self.location_id.id).free_qty
            if free_qty < line.return_qty:
                raise UserError(_(f'{line.product_id.name} not available in this location. Available quanity {free_qty}'))



    def create_return(self):
        self.ensure_one()
        self.check_product_availabilty()
        incoming_picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        return_picking_type = incoming_picking_type.return_picking_type_id
        picking = self.env['stock.picking'].create({
            'picking_type_id': return_picking_type.id,
            'partner_id': self.partner_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': incoming_picking_type.default_location_src_id.id,
            'scheduled_date': self.return_date,
            'origin': self.name,
            'company_id': self.company_id.id,
            'purchase_return_id': self.id,
        })
        for line in self.return_line_ids.filtered(lambda x: not x.is_roundoff):
            if line.return_qty > 0:
                move = self.env['stock.move'].create({
                    'name': self.name,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'product_uom_qty': line.return_qty,
                    'location_id': self.location_id.id,
                    'location_dest_id': incoming_picking_type.default_location_src_id.id,
                    'picking_id': picking.id,
                    'company_id': self.company_id.id,
                    'restrict_lot_id': line.lot_id.id if line.lot_id else False,
                    'to_refund': True,
                    'origin_returned_move_id':line.move_id.id,
                    'purchase_line_id': line.purchase_line_id.id,
                    'purchase_return_line_id': line.id,
                })
        picking.button_validate()
        self.return_picking_id = picking
        self.write({'state': 'done'})

    def create(self, vals):
        res = super(PurchaseReturn, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('purchase.return.seq') or _('New')
        return res
    
    @api.constrains('return_line_ids')
    def _check_return_qty(self):
        for line in self.return_line_ids.filtered(lambda x: not x.is_roundoff):
            if line.return_qty > line.product_qty:
                raise UserError(_('Return quantity must be less than or equal to product quantity.'))
            if line.return_qty == 0:
                raise UserError(_('Return quantity must be greater than 0.'))
            if line.return_qty > line.purchase_line_id.qty_received:
                raise UserError(_('Return quantity must be less than or equal to received quantity'))
            
    def _compute_picking_count(self):
        for record in self:
            record.picking_count = self.env['stock.picking'].search_count([('purchase_return_id', '=', record.id)])

    def _compute_refund_count(self):
        for record in self:
            record.refund_count = self.env['account.move'].search_count([('purchase_return_id', '=', record.id)])
            
    def view_pickings(self):
        pickings = self.env['stock.picking'].search([('purchase_return_id', '=', self.id)])
        if len(pickings) > 1:
            return {
                "name": _("Purchase Return"),
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "domain": [("id", "in", pickings.ids)],
                "target": "current",
                "view_mode": "list,form",
            }
        else:
            return {
                "name": _("Purchase Return"),
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "res_id": pickings.id,
                "target": "current",
                "view_mode": "form",
            }
        
    def view_refunds(self):
        refund_bills = self.env['account.move'].search([('purchase_return_id', '=', self.id)])
        if len(refund_bills) > 1:
            return {
                "name": _("Bill Refund"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "domain": [("id", "in", refund_bills.ids)],
                "target": "current",
                "view_mode": "list,form",
            }
        else:
            return {
                "name": _("Bill Refund"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": refund_bills.id,
                "target": "current",
                "view_mode": "form",
            }
        
    def view_purchase_orders(self):
        if len(self.purchase_ids) > 1:
            return {
                "name": _("Purchase Order"),
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "domain": [("id", "in", self.purchase_ids.ids)],
                "target": "current",
                "view_mode": "list,form",
            }
        else:
            return {
                "name": _("Purchase Order"),
                "type": "ir.actions.act_window",
                "res_model": "purchase.order",
                "res_id": self.purchase_ids[0].id,
                "target": "current",
                "view_mode": "form",
            }

    def _prepare_bill_refund_vals(self):
        lines = []
        total_credit_qty = sum((line.purchase_line_id.qty_invoiced - line.return_qty) for line in self.return_line_ids.filtered(lambda x: not x.is_roundoff))
        if total_credit_qty < 0:
            raise UserError(_("No quantities to create bill refund."))
        journal_id = self.env["account.journal"].search(
            [("type", "=", "purchase")], limit=1
        )
        for line in self.return_line_ids:
            to_credit_qty = line.return_qty
            po_line = line.purchase_line_id
            line_vals = {
                "display_type": "product",
                "product_id": line.product_id.id,
                "quantity": to_credit_qty,
                "product_uom_id": line.uom_id.id,
                "account_id": journal_id.default_account_id.id,
                "price_unit": po_line.price_unit or line.price_unit,
                "tax_ids": [(4, tax) for tax in po_line.taxes_id.ids],
                "purchase_line_id": po_line.id,
                "purchase_return_line_id": line.id,
                "is_refund": True,
                "discount": po_line.discount,
                "discount_fixed": po_line.discount_fixed,
                "is_roundoff": line.is_roundoff
            }
            lines.append((0, 0, line_vals))
        vals = {
            "move_type": "in_refund",
            "partner_id": self.partner_id.id,
            "invoice_line_ids": lines,
            "narration": f"Refund for Purchase Return:{self.name}",
            "invoice_date": fields.Date.today(),
            "purchase_return_id": self.id,
        }
        return vals

    def create_bill_refund(self):
        vals = self._prepare_bill_refund_vals()
        bill_refund_id = self.env["account.move"].create(vals)
        return {
            "name": _("Bill Refund"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": bill_refund_id.id,
            "view_mode": "form",
            "target": "current",
        }
    
    def unlink(self):
        picking_ids = self.picking_ids.filtered(lambda picking: picking.state != "cancel")
        bill_refund_ids = self.bill_refund_ids.filtered(lambda x: x.state != "cancel")
        if picking_ids or bill_refund_ids:
            raise UserError(
                _("Purchase return cannot be deleted as there exist related bill refunds/ pickings.")
            )
        return super(PurchaseReturn, self).unlink()
    
    def action_open_round_off_wizard(self):
        self.ensure_one()
        return {
            'name': _("Round-off"),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.return.round.off',
            'view_mode': 'form',
            'target': 'new',
        }
    

class PurchaseReturnLine(models.Model):
    _name = 'purchase.return.line'
    _description = 'Purchase Return Line'


    return_id = fields.Many2one('purchase.return', string='Return', ondelete='cascade')
    purchase_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line', store=True)
    product_id = fields.Many2one('product.product', string='Product', store=True)
    product_qty = fields.Float(string='Product Quantity')
    return_qty = fields.Float(string='Return Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', store=True)
    price_unit = fields.Float(string='Unit Price', store=True)
    lot_ids = fields.Many2many('stock.lot')
    lot_id = fields.Many2one('stock.lot', string='Lot')
    move_id = fields.Many2one('stock.move', string='Stock Move', store=True)
    product_code = fields.Char(related='product_id.default_code', string='Product Code', store=True)
    price_subtotal = fields.Float(string='Gross Total', compute='_compute_amount', store=True)
    price_total = fields.Float(string='Grand Total', compute='_compute_amount', store=True)
    price_tax = fields.Float(string='Tax', compute='_compute_amount', store=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', store=True)
    discount = fields.Float(string='Discount (%)', store=True)
    discount_fixed = fields.Float(string='Discount (Fixed)', store=True)
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount_amount', store=True)
    is_roundoff = fields.Boolean(string='Is Round-off', default=False)

    @api.depends('return_qty', 'price_unit', 'tax_ids', 'discount')
    def _compute_amount(self):
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            is_fixed_discount = False
            if line.discount_fixed > 0:
                base_line['discount'] = line.discount_fixed
                is_fixed_discount = True
            self.env['account.tax'].with_context(is_fixed_discount=is_fixed_discount)._add_tax_details_in_base_line(base_line, line.return_id.company_id)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal
    
    def _prepare_base_line_for_taxes_computation(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            tax_ids=self.tax_ids,
            quantity=self.return_qty,
            partner_id=self.return_id.partner_id,
            currency_id=self.purchase_line_id.currency_id or self.return_id.company_id.currency_id,
            rate=self.purchase_line_id.order_id.currency_rate,
            price_unit=self.price_unit,
            discount=self.discount,
        )

    @api.depends('return_qty', 'price_unit', 'price_subtotal')
    def _compute_discount_amount(self):
        for line in self:
            line.discount_amount = (line.return_qty * line.price_unit) - line.price_subtotal

    @api.onchange('return_qty')
    def _onchange_return_qty(self):
        if self.return_qty > self.product_qty:
            raise UserError(_('Return quantity must be less than or equal to product quantity.'))