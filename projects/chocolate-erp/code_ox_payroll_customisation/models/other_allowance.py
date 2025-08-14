from odoo import models, fields, api, _
from odoo.exceptions import UserError


class OtherAllowanceType(models.Model):
    _name = 'other.allowance.type'
    _description = 'Other Allowance Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', tracking=True)
    code = fields.Char(string='Code', tracking=True)


class EmployeeOtherAllowance(models.Model):
    _name = 'employee.other.allowance'
    _description = 'Employee Other Allowance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', default='New')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    date = fields.Date(string='Date', default=fields.Date.today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm')
    ], string='State', default='draft', tracking=True)
    note = fields.Text(string='Note')
    allowance_type_id = fields.Many2one('other.allowance.type', string='Allowance Type')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)

    def action_confirm(self):
        self.name = self.env['ir.sequence'].next_by_code(
           'employee.other.allowance') or _('New')
        self.write({'state': 'confirm'})

    def unlink(self):
        for rec in self:
            if rec.state == 'confirm':
                raise UserError(_("You cannot delete confirmed records."))
        return super(EmployeeOtherAllowance, self).unlink()