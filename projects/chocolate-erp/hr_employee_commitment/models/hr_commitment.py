from odoo import models, fields
from datetime import timedelta


class HrCommitmentType(models.Model):
    _name = 'hr.commitment.type'
    _description = 'Commitment Type'

    name = fields.Char(string='Type of Commitment', required=True)


class HrCommitments(models.Model):
    _name = 'hr.commitment'
    _description = 'HR Commitment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Commitment Title', required=True)
    date = fields.Date(default=fields.Date.today)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    commitment_type_id = fields.Many2one('hr.commitment.type')
    planned_date = fields.Date()
    fullfilled_date = fields.Date()
    commitment_description = fields.Text()
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    state = fields.Selection([('pending', 'Pending'), ('completed', 'Completed'), 
                              ('cancelled', 'Cancelled'),], string='Status', default='pending')
    notes = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment')

    def mark_as_done(self):
        self.state = 'completed'
        self.fullfilled_date = fields.Date.today()

    def send_commitment_reminders(self):
        """Find commitments due in 15 days and remind HR manager."""
        today = fields.Date.today()
        remind_date = today + timedelta(days=15)
        commitments = self.search([('planned_date', '=', remind_date), ('state', '=', 'pending')])

        hr_manager_group = self.env.ref('hr.group_hr_manager')  # Reference to HR Manager group
        hr_managers = hr_manager_group.users.mapped('partner_id')  # Get all HR managers' partner records

        for commitment in commitments:
            if hr_managers:
                commitment.message_post(
                    body=f"Reminder: Commitment '{commitment.name}' is due on {commitment.planned_date}.",
                    subject="Commitment Reminder",
                    partner_ids=hr_managers.ids  # Use a plain list of partner IDs
                )

                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get('hr.commitment').id,
                    'res_id': commitment.id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'summary': "Follow up on commitment",
                    'note': f"Reminder: Commitment '{commitment.name}' is due in 15 days.",
                    'user_id': commitment.user_id.id, 
                    'date_deadline': remind_date,
                })


