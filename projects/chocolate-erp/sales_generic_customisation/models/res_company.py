from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    promotional_expense_account_id = fields.Many2one(
        "account.account",
        string="Default Expense Account",
        check_company=True,
        help="The company's default promotional expense account used when a promotional sale created.",
    )