from odoo import models, fields, _, api
from odoo.exceptions import UserError

class DietitianAvailableDays(models.Model):
    _name = 'dietitian.available.days'

    name = fields.Char(string="Day", required=True)

class DietitianTimeSlot(models.Model):
    _name = 'dietitian.time.slot'

    name = fields.Char(string="Time Slot", compute="_compute_name", store=True)
    dietitian_id = fields.Many2one('hr.employee', string="Dietitian", required=True)
    start_time = fields.Float(string="Start Time", required=True)
    end_time = fields.Float(string="End Time", required=True)

    @api.depends('start_time', 'end_time')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.start_time:.2f} - {record.end_time:.2f}"

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employee_type = fields.Selection(
        selection_add=[('dietitian', 'Dietitian'),('driver', 'Driver')],
        ondelete={'dietitian': 'set default', 'driver':'set default'})

    area_of_speciality_ids = fields.One2many('hr.area.speciality', 'dietitian_id', string="Area of Speciality")
    dietitian_available_days = fields.Many2many(
        'dietitian.available.days', 
        string="Available Days"
    )
    dietitian_time_slots = fields.One2many(
        'dietitian.time.slot', 
        'dietitian_id', 
        string="Time Slots"
    )


    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
            raise UserError(_("You don't have access to delete this record."))
        return super(HrEmployee, self).unlink()
    
class AreaOfSpeciality(models.Model):
    _name = 'hr.area.speciality'
    _description = 'Area of Speciality'

    dietitian_id = fields.Many2one('hr.employee', string="Dietitian")
    name = fields.Char(string="Speciality", required=True)
