from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    unrealized_branch_profit_account_id = fields.Many2one(
        'account.account', string="Unrealized Branch Profit Account", check_company=True,
        help="Account used to record unrealized profits from branch transfers."
    )
    branch_suspense_account_id = fields.Many2one(
        'account.account', string="Branch Suspense", check_company=True, help="The company's suspense account for branch transfers.")
    branch_transfer_cost_account_id = fields.Many2one(
        'account.account', string="Branch Transfer Cost", check_company=True, help="The company's cost account for branch transfers."
    )
    inter_branch_profit_account_id = fields.Many2one(
        'account.account', string="Inter Branch Profit Account", check_company=True, help="The company's inter-branch profit account."
    )
    branch_code = fields.Char(
        string="Branch Code", help="The code of the branch for this company.")