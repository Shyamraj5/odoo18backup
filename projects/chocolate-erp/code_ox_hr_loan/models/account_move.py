from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    loan_id = fields.Many2one('employee.loan')