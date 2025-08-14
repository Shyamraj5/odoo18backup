from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import ValidationError


class EmployeeLoanType(models.Model):
    _name = 'employee.loan.type'
    _description = 'Employee Loan Type'

    name = fields.Char(required=True)
    amount_limit = fields.Float()
    loan_term = fields.Integer()
    interest_rate = fields.Float()
    apply_interest = fields.Boolean(default=False)
    loan_account_id = fields.Many2one('account.account', string='Loan Account')
    interest_account_id = fields.Many2one('account.account', string='Interest Account')
    journal_id = fields.Many2one('account.journal', string='Journal')


class EmployeeLoan(models.Model):
    _name = 'employee.loan'
    _description = 'Employee Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, default='New')
    employee_id = fields.Many2one('hr.employee')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id')
    loan_type_id = fields.Many2one('employee.loan.type')
    loan_amount = fields.Float()
    interest_amount = fields.Float(compute='compute_interest_amount', store=True)
    paid_amount = fields.Float(compute='compute_remaining_and_paid_amount')
    remaining_amount = fields.Float(compute='compute_remaining_and_paid_amount')
    amount_total = fields.Float(compute='compute_total', store=True)
    date = fields.Date(default=fields.Date.today)
    start_date = fields.Date()
    term = fields.Integer(related='loan_type_id.loan_term')
    end_date = fields.Date()
    interest_rate = fields.Float(related='loan_type_id.interest_rate')
    reason = fields.Text()
    installment_line_ids = fields.One2many('employee.loan.installment', 'loan_id')
    state = fields.Selection([('draft', 'Draft'), ('submit_request', 'Submit Request'), 
                              ('hr_approval', 'HR Approval'), ('done', 'Done'), ('rejected', 'Rejected')], 
                              default='draft', tracking=True)
    

    @api.onchange('loan_type_id', 'start_date')
    def get_end_date(self):
        if self.loan_type_id and self.start_date:
            self.end_date = self.start_date + relativedelta(months=self.term)

    @api.onchange("loan_type_id")
    def _onchange_loan_type(self):
        self.loan_amount = self.loan_type_id.amount_limit

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
           'employee.loan') or _('New')
        res = super(EmployeeLoan, self).create(vals)
        return res
    
    def compute_installment(self):
        self.installment_line_ids = False
        installment_amount = self.loan_amount/self.term
        installment_values = []
        for i in range(1, self.term+1):
            installment_date = self.start_date + relativedelta(months=i)
            installment_values.append({
                'installment_amount': installment_amount,
                'date': installment_date,
                'interest_amount': installment_amount * self.interest_rate/100,
                'total_amount': installment_amount + installment_amount * self.interest_rate/100,
                'paid_amount': 0,
                'loan_id': self.id
            })
        self.env['employee.loan.installment'].create(installment_values)

    def submit_request(self):
        self.state ='submit_request'

    def hr_approval(self):
        self.state ='hr_approval'

    def reject_loan(self):
        self.state = 'rejected'

    @api.depends('loan_amount', 'installment_line_ids', 'amount_total')
    def compute_remaining_and_paid_amount(self):
        for loan in self:
            loan.remaining_amount = loan.amount_total - sum(line.paid_amount for line in loan.installment_line_ids)
            loan.paid_amount = sum(line.paid_amount for line in loan.installment_line_ids)

    @api.depends('loan_amount', 'interest_rate')
    def compute_interest_amount(self):
        for loan in self:
            loan.interest_amount = loan.loan_amount * loan.interest_rate/100

    @api.depends('loan_amount', 'interest_amount')
    def compute_total(self):
        for loan in self:
            loan.amount_total = loan.loan_amount + loan.interest_amount

    def pay_loan(self):
        for loan in self:
            journal_id = loan.loan_type_id.journal_id
            credit_account_id = journal_id.default_account_id.id
            debit_account_id = loan.loan_type_id.loan_account_id.id
            amount = loan.loan_amount
            move = {
                'journal_id': journal_id.id,
                'ref': loan.name,
                'date': date.today(),
                'loan_id': loan.id,
                'line_ids': [(0, 0, {
                    'name': loan.name,
                    'account_id': debit_account_id,
                    'debit': amount,
                    'credit': 0.0,
                    'partner_id': loan.employee_id.user_partner_id.id
                }), (0, 0, {
                    'name': loan.name,
                    'account_id': credit_account_id,
                    'debit': 0.0,
                    'credit': amount,
                    'partner_id': loan.employee_id.user_partner_id.id
                })]
            }
            account_move = self.env['account.move'].create(move)
            account_move.action_post()
            loan.state = 'done'

    @api.constrains('loan_amount', 'loan_type_id')
    def check_loan_amount(self):
        for loan in self:
            if loan.loan_amount > loan.loan_type_id.amount_limit:
                raise ValidationError(_('Loan amount exceeds the limit!'))
            
    def action_view_journal(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entries'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('loan_id', '=', self.id)],
        }
            
    def unlink(self):
        for loan in self:
            if loan.state != 'draft':
                raise ValidationError(_('You can only delete draft loans!'))
        return super(EmployeeLoan, self).unlink()
    
    
class EmployeeLoanInstallment(models.Model):
    _name = 'employee.loan.installment'
    _description = 'Employee Loan Installment'

    loan_id = fields.Many2one('employee.loan')
    installment_amount = fields.Float()
    interest_amount = fields.Float()
    total_amount = fields.Float()
    paid_amount = fields.Float()
    date = fields.Date()
    paid = fields.Boolean(default=False)
    





