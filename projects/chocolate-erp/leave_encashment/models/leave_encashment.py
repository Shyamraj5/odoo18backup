from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from lxml import etree

class LeaveEncashment(models.Model):
    _name = 'leave.encashment'
    _description = 'Leave Encashment'

    def _get_employee_id(self):
        employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee_rec.id

    name = fields.Char(string='Reference', readonly=True, default=lambda self: 'New')
    employee_id = fields.Many2one('hr.employee', string='Employee',default=_get_employee_id)
    leave_encash = fields.Float(string='Leave Encashed')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    amount = fields.Float(string='Amount')
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id', readonly=True)
    job_position = fields.Char(string='Job Position', related='employee_id.job_title', readonly=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type')
    leave_pending = fields.Float(string='Leave Pending', compute='_compute_leave_pending', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('approved', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True)
    contract_id = fields.Many2one('hr.contract')

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_approve(self):
        if self.amount <= 0:
            raise UserError(_('Amount should be greater than 0'))
        hr_allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('holiday_status_id', '=', self.leave_type_id.id)
        ])
        self.env['hr.leave.encashment.history'].create({
            'leave_encashment_id': self.id,
            'leave_allocation_id': hr_allocations[0].id
        })
        self.write({'state': 'approved'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.constrains('leave_encash', 'leave_pending')
    def _check_leave_encashment(self):
        for record in self:
            if record.leave_encash > record.leave_pending:
                raise ValidationError("The Leave Encashment cannot be greater than the Leave Pending.")

    @api.depends('employee_id', 'leave_type_id')
    def _compute_leave_pending(self):
        for record in self:
            if record.employee_id and record.leave_type_id:
                self.env.cr.execute("""
                    SELECT COALESCE(SUM(number_of_days), 0)
                    FROM hr_leave_employee_type_report
                    WHERE employee_id = %s
                    AND leave_type = %s
                    AND holiday_status = 'left'
                """, (record.employee_id.id, record.leave_type_id.id))
                result = self.env.cr.fetchone()
                record.leave_pending = result[0] if result else 0.0
            else:
                record.leave_pending = 0.0

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('leave.encashment.seq') or _('New')
        return super(LeaveEncashment, self).create(vals)
    
    @api.onchange('employee_id', 'leave_encash')
    def get_encashment_amount(self):
        if self.employee_id and self.leave_encash:
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)
            self.contract_id = contract.id if contract else False
            if contract and contract.wage:
                working_days_per_month = 30  # Adjust this if necessary
                daily_wage = contract.wage / working_days_per_month
                self.amount = daily_wage * self.leave_encash
            else:
                self.amount = 0.0