from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    credit_note_account_id = fields.Many2one("account.account", string="Default Credit Note Account")
