from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    days_limit = fields.Integer(string="Days")
    credit_approval_state = fields.Selection(
        selection=[('draft','Draft'),('approved','Approved')],string="State",default='draft')
    
    def approve_credit_limit(self):
        if self.credit_approval_state == 'draft':
            self.credit_approval_state = 'approved'