from odoo import models,fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        loan_installment, monthly_deduction = self._get_loan_monthly_deduction(contracts.employee_id.id, date_from, date_to)
        deduction_category = self.env['hr.salary.rule.category'].search([('code', '=', 'DED')], limit=1)
        if not deduction_category:
            deduction_category = self.env['hr.salary.rule.category'].create({
                'name': 'Deduction',
                'code': 'DED',
            })
        loan_deduction_rule = self.env['hr.salary.rule'].search([('code', '=', 'LOAN')], limit=1)
        if not loan_deduction_rule:
            amount_python_compute = 'result = inputs.LOAN.amount\nresult_name = inputs.LOAN.name'
            condition_python = 'result = inputs.LOAN'
            loan_deduction_rule = self.env['hr.salary.rule'].create({
                'name': 'Loan or Advance',
                'code': 'LOAN',
                'category_id': deduction_category.id,
                'sequence': 150,
                'condition_select': 'python',
                'condition_python': condition_python,
                'amount_select': 'code',
                'amount_python_compute': amount_python_compute,
                'appears_on_payslip': True,
            })
        
        if monthly_deduction > 0:
            if self.struct_id and loan_deduction_rule not in self.struct_id.rule_ids:
                self.struct_id.write({'rule_ids': [(4, loan_deduction_rule.id)]})
            line_exists = self.input_line_ids.filtered(lambda l: l.code == 'LOAN')
            if line_exists:
                line_exists.amount = -1 * monthly_deduction
            loan_line = {
                'name': 'Loan/ Advance',
                'code': 'LOAN',
                'amount': -1 * monthly_deduction,
                'contract_id': contracts.id,
                'loan_installment_id': loan_installment
            }
            res += [loan_line]
        return res

    def _get_loan_monthly_deduction(self, employee, date_from, date_to):
        """Fetch monthly deduction."""
        if not employee:
            return 0.0
        sql_query = f""" 
                SELECT el.employee_id, eli.id as intallment, SUM(eli.total_amount) FROM employee_loan_installment eli
                INNER JOIN employee_loan el ON el.id = eli.loan_id
                WHERE el.employee_id = %s AND eli.date BETWEEN %s AND %s AND el.state = 'done' AND eli.paid_amount = 0
                GROUP BY el.employee_id, eli.id
                """
        self.env.cr.execute(sql_query, (employee, date_from, date_to))
        result = self.env.cr.fetchone()
        return (round(result[1]), round(result[2])) if result else (False, 0.0)
    
    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_installment_id:
                line.loan_installment_id.paid = True
                line.loan_installment_id.paid_amount = -1 * line.amount
                line.loan_installment_id.loan_id.compute_remaining_and_paid_amount()
        return super(HrPayslip, self).action_payslip_done() 