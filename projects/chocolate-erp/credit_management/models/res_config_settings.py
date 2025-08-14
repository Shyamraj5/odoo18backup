from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    days_limit = fields.Integer(
        string="Days Limit",
        default=0,
    )
    account_use_days_limit = fields.Boolean(
        string='Days Limit on Invoices',
        default=False,
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    days_limit = fields.Integer(
        related='company_id.days_limit',
        string="Days Limit",
        readonly=False,
    )
    account_use_days_limit = fields.Boolean(
        related='company_id.account_use_days_limit',
        string='Days Limit on Invoices',
        readonly=False,
    )