from odoo import api, models, fields


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    kilometer = fields.Float(string='Kilometer')
