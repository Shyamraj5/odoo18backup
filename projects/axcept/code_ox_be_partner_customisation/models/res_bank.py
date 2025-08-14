from odoo import models, fields

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    account_type = fields.Selection([
        ('savings', 'Savings'),
        ('current', 'Current'),
        ('salary', 'Salary'),
        ('other', 'Other'),
    ], string="Account Type")

class ResBank(models.Model):
    _inherit = 'res.bank'

    branch = fields.Char(string="Branch")
