from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    promotional_expense_account_id = fields.Many2one('account.account', 
                                            related='company_id.promotional_expense_account_id', 
                                            check_company=True,
                                            readonly=False,
                                            string='Promotional Expense Account')