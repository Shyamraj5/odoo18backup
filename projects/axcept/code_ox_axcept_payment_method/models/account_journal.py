from odoo import models, fields, api

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    default_bank_payment_method = fields.Boolean(
        default=False,
        string='Default Bank Payment Method',
        help="If checked, this journal will be used as the default bank payment method."
    )