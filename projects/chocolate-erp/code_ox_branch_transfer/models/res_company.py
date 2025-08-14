from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    margin_account_id = fields.Many2one(
        "account.account",
        string="Branch Transfer Margin Account",
        check_company=True,
        help="The company's profit margin account for branch transfer.",
    )