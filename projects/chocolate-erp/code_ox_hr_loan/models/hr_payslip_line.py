from odoo import models, fields

class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.input'

    loan_installment_id = fields.Many2one('employee.loan.installment', store=True)