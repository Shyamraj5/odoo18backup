from odoo import models, fields,api, _ 
from odoo.exceptions import UserError


class DietitianAppointmentHistory(models.Model):
    _name = 'dietitian.appointment.history'
    _description = 'Dietitian Appointment History'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Name", required=True, copy=False, readonly=True, default="New")
    dietitian_id = fields.Many2one('hr.employee', string="Dietitian", required=True, domain=[('employee_type', '=', 'dietitian')], tracking=True)
    date = fields.Date(string="Appointment Date", required=True)
    time_slot_id = fields.Many2one('dietitian.time.slot', string="Time Slot", required=True, domain="[('dietitian_id', '=', dietitian_id)]", tracking=True)
    patient_id = fields.Many2one('res.partner', string="Patient", required=True, domain=[('parent_id', '=', False)], tracking=True)
    dietitian_notes = fields.Text(string="Dietitian Notes", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft', tracking=True, copy=False)

    @api.depends('time_slot_id')
    def _compute_times(self):
        for record in self:
            if record.time_slot_id:
                record.start_time = record.time_slot_id.start_time
                record.end_time = record.time_slot_id.end_time

    @api.onchange('dietitian_id', 'date')
    def _onchange_dietitian_and_date(self):
        # Filter available time slots for the selected dietitian and date
        if self.dietitian_id and self.date:
            available_slots = self.env['dietitian.time.slot'].search([
                ('dietitian_id', '=', self.dietitian_id.id)
            ])
            self.time_slot_id = False  # Clear the selection
            return {'domain': {'time_slot_id': [('id', 'in', available_slots.ids)]}}
        else:
            self.time_slot_id = False
            return {'domain': {'time_slot_id': []}}

    @api.constrains('dietitian_id', 'date', 'time_slot_id')
    def _check_slot_availability(self):
        for record in self:
            overlapping_appointments = self.search([
                ('dietitian_id', '=', record.dietitian_id.id),
                ('date', '=', record.date),
                ('time_slot_id', '=', record.time_slot_id.id),
                ('id', '!=', record.id),
            ])
            if overlapping_appointments:
                raise ValidationError("This time slot is already booked.")
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(DietitianAppointmentHistory, self).unlink()