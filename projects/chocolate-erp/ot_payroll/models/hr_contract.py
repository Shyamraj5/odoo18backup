from odoo import models,fields

class HrContract(models.Model):
    _inherit = "hr.contract"

    overtime_hourly_wage = fields.Float(string="Over Time Hourly Wage")
    is_overtime_allowed = fields.Boolean(related='employee_id.is_overtime_allowed')