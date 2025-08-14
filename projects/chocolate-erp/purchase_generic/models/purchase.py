from odoo import models, fields,api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    import_purchase = fields.Boolean(default=False)
    ministry_approval_ids = fields.Many2many('ir.attachment', 'ministry_approval', 'purchase_id', 'attachment_id')
    health_approval_ids = fields.Many2many('ir.attachment', 'health_approval', 'purchase_id', 'attachment_id')
    labeling_approval_ids = fields.Many2many('ir.attachment', 'labeling_approval', 'purchase_id', 'attachment_id')
    total_discount = fields.Monetary(string='Discount Amount', compute='_compute_discount_amount', store=True, readonly=True)
    vendor_code = fields.Char(string="Vendor Code")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.vendor_code = self.partner_id.vendor_code
        else:
            self.vendor_code = False
    
    @api.onchange('vendor_code')
    def _onchange_vendor_code(self):
        if self.vendor_code:
            self.partner_id = self.env['res.partner'].search([('vendor_code', '=', self.vendor_code)], limit=1)
        else:
            self.partner_id = False

    @api.onchange('import_purchase')
    def _onchange_import_purchase(self):
        if self.import_purchase:
            return {'domain': {'partner_id': [('vendor_type', '=', 'import_vendor')]}}
        else:
            return {'domain': {'partner_id': [('vendor_type', '=', 'local_vendor')]}}
        
    @api.depends('order_line.discount_amount')
    def _compute_discount_amount(self):
        for order in self:
            order.total_discount = sum(order.order_line.mapped('discount_amount'))

    @api.depends('order_line.price_subtotal', 'currency_id', 'company_id', 'total_discount')
    def _compute_tax_totals(self):
        res = super(PurchaseOrder, self)._compute_tax_totals()
        AccountTax = self.env['account.tax']
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.is_discount)
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
            order.tax_totals['total_amount_currency'] = order.tax_totals['total_amount_currency'] + global_discount
            if 'subtotals' in order.tax_totals:
                for subtotal in order.tax_totals['subtotals']:
                    if subtotal.get('name') == 'Untaxed Amount':
                        subtotal['name'] = 'Taxable'
        return res
    
    def send_to_multiple_vendors(self):
        try:
            if self.env.context.get('send_rfq', False):
                template_id = self.env.ref('purchase.email_template_edi_purchase')
            else:
                template_id = self.env.ref('purchase.email_template_edi_purchase_done')
        except ValueError:
            template_id = False
        for record in self.alternative_po_ids:
            template_id.send_mail(record.id)
            if record.state == 'draft':
                record.write({'state': 'sent'})
        return True
    
    def action_create_invoice(self):
        res = super(PurchaseOrder, self).action_create_invoice()
        for order in self:
            bill = self.env['account.move'].browse(res['res_id'])
            for move_line in bill.invoice_line_ids:
                move_line.write({
                    'is_discount': move_line.purchase_line_id.is_discount
                })
            for code in self:
                bill.write({'vendor_code': code.vendor_code if code.vendor_code else False})
        return res
    
    def create(self, vals_list):
        po = super(PurchaseOrder, self).create(vals_list)
        if self.env.context.get('default_confirm_purchase', False):
            po.button_confirm()
        return po
            

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    expiration_date = fields.Datetime(compute='get_expiration_date')
    internal_reference = fields.Char(
        string='Internal Reference',
        related='product_id.default_code',
        store=True,
        readonly=True,
    )
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount_amount', store=True)
    is_discount = fields.Boolean(string='Is Discount', default=False)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="product_uom_domain")
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

    def get_expiration_date(self):
        for line in self:
            if line.product_id.tracking == 'lot':
                moves = line.move_ids
                lots = moves.mapped('lot_ids')
                if lots:
                    line.expiration_date = lots[0].expiration_date
                else:
                    line.expiration_date = False
            else:
                line.expiration_date = False

    @api.depends('product_qty', 'price_unit', 'price_unit_discounted')
    def _compute_discount_amount(self):
        for line in self:
            line.discount_amount = line.product_qty * (line.price_unit - line.price_unit_discounted)
            if line.is_discount:
                line.discount_amount = -1 * line.price_subtotal

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type != 'consu':
            return res

        price_unit = self._get_stock_move_price_unit()
        qty = self._get_qty_procurement()

        move_dests = self.move_dest_ids or self.move_ids.move_dest_ids
        move_dests = move_dests.filtered(lambda m: m.state != 'cancel' and not m._is_purchase_return())

        if not move_dests:
            qty_to_attach = 0
            qty_to_push = self.product_qty - qty
        else:
            move_dests_initial_demand = self._get_move_dests_initial_demand(move_dests)
            qty_to_attach = move_dests_initial_demand - qty
            qty_to_push = self.product_qty - move_dests_initial_demand

        if float_compare(qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            res.append(self._prepare_stock_move_vals(picking, price_unit, self.product_qty, self.product_uom))
        if not float_is_zero(qty_to_push, precision_rounding=self.product_uom.rounding):
            extra_move_vals = self._prepare_stock_move_vals(picking, price_unit, self.product_qty, self.product_uom)
            extra_move_vals['move_dest_ids'] = False  # don't attach
            res.append(extra_move_vals)
        return res