from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        incentive_amount = self._get_incentive_bonus(contracts.employee_id.user_id.id, date_from, date_to)
        
        allowance_category = self.env['hr.salary.rule.category'].search(
                [('code', '=', 'ALW')], limit=1
            )
        if not allowance_category:
            allowance_category = self.env['hr.salary.rule.category'].create({
                'name': 'Allowance',
                'code': 'ALW',
            })
        
        incentive_rule = self.env['hr.salary.rule'].search(
            [('code', '=', 'INCENTIVE')], limit=1
        )
        if not incentive_rule:
            amount_python_compute = 'result = inputs.INCENTIVE.amount\nresult_name = inputs.INCENTIVE.name'
            condition_python = 'result = inputs.INCENTIVE'
            incentive_rule = self.env['hr.salary.rule'].create({
                'name': 'Incentive',
                'code': 'INCENTIVE',
                'category_id': allowance_category.id,
                'sequence': 10,
                'condition_select': 'python',
                'condition_python': condition_python,
                'amount_select': 'code',
                'amount_python_compute': amount_python_compute,
                'appears_on_payslip': True,
            })
        
        if incentive_amount > 0:
            if self.struct_id and incentive_rule not in self.struct_id.rule_ids:
                self.struct_id.write({'rule_ids': [(4, incentive_rule.id)]})
            line_exists = self.input_line_ids.filtered(lambda l: l.code == 'INCENTIVE')
            if line_exists:
                line_exists.amount = incentive_amount
            incentive_line = {
                'name': 'Incentive',
                'code': 'INCENTIVE', 
                'amount': incentive_amount,
                'contract_id': contracts.id,
            }
            res += [incentive_line]
        return res


    def _get_incentive_bonus(self, employee, date_from, date_to):
        """Fetch incentive bonus for the employee within the given period."""
        if not employee:
            return 0.0
        self.env.cr.execute("""
            SELECT COALESCE(SUM(incentive_bonus), 0.0)
            FROM incentive_sql_view
            WHERE sales_person = %s
            AND date >= %s
            AND date <= %s
        """, (employee, date_from, date_to))
        result = self.env.cr.fetchone()
        return float(result[0]) if result else 0.0    

