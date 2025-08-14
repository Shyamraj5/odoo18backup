from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Payable",
        domain="[('deprecated', '=', False)]",
        help="This account will be used instead of the default one as the payable account for the current partner",
        ondelete='restrict')
    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
        string="Account Receivable",
        domain="[('deprecated', '=', False)]",
        help="This account will be used instead of the default one as the receivable account for the current partner",
        ondelete='restrict')