# models/res_config_settings.py

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    unrealized_branch_profit_account_id = fields.Many2one(
        'account.account', string="Unrealized Branch Profit Account", related='company_id.unrealized_branch_profit_account_id',
        check_company=True, readonly=False, help="Account used to record unrealized profits from branch transfers."
    )
    branch_suspense_account_id = fields.Many2one(
        'account.account', string="Branch Suspense", related='company_id.branch_suspense_account_id',
        check_company=True, readonly=False, help="The company's suspense account for branch transfers."
    )
    branch_transfer_cost_account_id = fields.Many2one(
        'account.account', string="Branch Transfer Cost", related='company_id.branch_transfer_cost_account_id',
        check_company=True, readonly=False, help="The company's cost account for branch transfers."
    )
    inter_branch_profit_account_id = fields.Many2one(
        'account.account', string="Inter Branch Profit Account", related='company_id.inter_branch_profit_account_id',
        check_company=True, readonly=False, help="The company's inter-branch profit account."
    )
