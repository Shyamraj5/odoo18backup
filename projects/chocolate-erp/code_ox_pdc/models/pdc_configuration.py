from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pdc_account_receivable_id = fields.Many2one(
        string="PDC Account Receivable",
        comodel_name="account.account",
        company_dependent=True,
        config_parameter="code_ox_pdc.pdc_account_receivable_id",
    )
    pdc_account_payable_id = fields.Many2one(
        string="PDC Account Payable",
        comodel_name="account.account",
        company_dependent=True,
        config_parameter="code_ox_pdc.pdc_account_payable_id",
    )
    issued_journal_id = fields.Many2one(
        string="Issued Journal",
        comodel_name="account.journal",
        config_parameter="code_ox_pdc.issued_journal_id",
    )
    received_journal_id = fields.Many2one(
        string="Received Journal",
        comodel_name="account.journal",
        ondelete="restrict",
        config_parameter="code_ox_pdc.received_journal_id",
    )
