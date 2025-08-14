from odoo import models, fields

class AccountAsset(models.Model):
    _inherit = 'account.asset.asset'

    employee_id = fields.Many2one('hr.employee',string='Employee')
    