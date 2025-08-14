from odoo import fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"

    is_pdc = fields.Boolean(string="Is PDC")