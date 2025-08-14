from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    total_discount = fields.Float(string='Total Discount', compute='_compute_total_discount', store=True)
    vendor_code = fields.Char(string='Vendor Code')
    customer_code = fields.Char(string='Customer Code')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.vendor_code = self.partner_id.vendor_code
            self.customer_code = self.partner_id.customer_code
        else:
            self.vendor_code = False
            self.customer_code = False

    @api.onchange('vendor_code')
    def _onchange_vendor_code(self):
        if self.vendor_code:
            self.partner_id = self.env['res.partner'].search([('vendor_code', '=', self.vendor_code)], limit=1)
        else:
            self.partner_id = False
    
    @api.onchange('customer_code')
    def _onchange_customer_code(self):
        if self.customer_code:
            self.partner_id = self.env['res.partner'].search([('customer_code', '=', self.customer_code)], limit=1)
        else:
            self.partner_id = False


    @api.depends('invoice_line_ids.discount_amount')
    def _compute_total_discount(self):
        for inv in self:
            inv.total_discount = sum(inv.invoice_line_ids.mapped('discount_amount'))

    def _compute_tax_totals(self):
        res = super(AccountMove, self)._compute_tax_totals()
        for inv in self:
            if inv.tax_totals:
                if inv.total_discount > 0:
                    inv.tax_totals['discount'] = inv.total_discount
                global_discount = sum(inv.invoice_line_ids.filtered(lambda x: x.is_discount == True).mapped('price_subtotal'))
                round_off = sum(inv.invoice_line_ids.filtered(lambda x: x.is_roundoff == True).mapped('price_subtotal'))
                if round_off:
                    inv.tax_totals['round_off'] = round_off
                if 'subtotals' in inv.tax_totals:
                    for subtotal in inv.tax_totals['subtotals']:
                        if subtotal.get('name') == 'Untaxed Amount':
                            subtotal['name'] = 'Taxable'
                        subtotal['base_amount_currency'] -= (global_discount + round_off)
        return res