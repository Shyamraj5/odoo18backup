from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    pdc_account_receivable_id = fields.Many2one(
        string="PDC Account Receivable",
        comodel_name="account.account",
        company_dependent=True,
    )
    pdc_account_payable_id = fields.Many2one(
        string="PDC Account Payable",
        comodel_name="account.account",
        company_dependent=True,
    )
    pdc_discount_account_id = fields.Many2one(
        string="PDC Discount Account",
        comodel_name="account.account",
        company_dependent=True
    )
    issued_journal_id = fields.Many2one(
        string="Issued Journal",
        comodel_name="account.journal",
        company_dependent=True,
    )
    received_journal_id = fields.Many2one(
        string="Received Journal",
        comodel_name="account.journal",
        company_dependent=True,
    )