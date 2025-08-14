from odoo import fields, models

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    allow_leave_encashment = fields.Boolean(string="Allow Leave Encashment", default=False)
