from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_overtime_allowed = fields.Boolean(string="Is OverTime Allowed",default=False)