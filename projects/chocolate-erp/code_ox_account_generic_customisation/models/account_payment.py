from odoo import models, fields, _, api
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    ref_date = fields.Date(string='Reference Date', tracking=True)
    remarks = fields.Char(string='Remarks', tracking=True)
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


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        res = super(AccountPaymentRegister, self).action_create_payments()
        for wizard in self:
            if wizard.amount > wizard.source_amount_currency and wizard.source_amount_currency > 0:
                raise UserError(_("The payment amount cannot be greater than invoice amount."))
        return res