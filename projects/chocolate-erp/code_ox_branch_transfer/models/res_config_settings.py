from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    margin_account_id = fields.Many2one('account.account', 
                                            related='company_id.margin_account_id', 
                                            check_company=True,
                                            readonly=False,
                                            string='Branch Transfer Margin Account')