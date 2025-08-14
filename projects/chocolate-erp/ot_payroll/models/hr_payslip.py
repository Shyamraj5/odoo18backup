from odoo import models,fields,api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        overtime_hours = self._get_overtime_wage(contracts.employee_id.id, date_from,date_to)
        overtime_amount = overtime_hours * contracts.overtime_hourly_wage if contracts else 0.0

        allowance_category = self.env['hr.salary.rule.category'].search(
                [('code', '=', 'ALW')], limit=1
            )
        if not allowance_category:
            allowance_category = self.env['hr.salary.rule.category'].create({
                'name': 'Allowance',
                'code': 'ALW',
            })
        
        overtime_rule = self.env['hr.salary.rule'].search(
            [('code', '=', 'OT_WAGE')], limit=1
        )
        if not overtime_rule:
            amount_python_compute = 'result = inputs.OT_WAGE.amount\nresult_name = inputs.OT_WAGE.name'
            condition_python = 'result = inputs.OT_WAGE'
            overtime_rule = self.env['hr.salary.rule'].create({
                'name': 'Overtime Wage',
                'code': 'OT_WAGE',
                'category_id': allowance_category.id,
                'sequence': 10,
                'condition_select': 'python',
                'condition_python': condition_python,
                'amount_select': 'code',
                'amount_python_compute': amount_python_compute,
                'appears_on_payslip': True,
            })
        
        if overtime_amount > 0:
            if self.struct_id and overtime_rule not in self.struct_id.rule_ids:
                self.struct_id.write({'rule_ids': [(4, overtime_rule.id)]})
            line_exists = self.input_line_ids.filtered(lambda l: l.code == 'INCENTIVE')
            if line_exists:
                line_exists.amount = overtime_amount
            over_time_line = {
               'name': 'Overtime Wage',
                'code': 'OT_WAGE', 
                'amount': overtime_amount,
                'contract_id': contracts.id,
            }
            res += [over_time_line]
        return res

        
    def _get_overtime_wage(self, employee, date_from, date_to):
        """Fetch Overtime Wage for the employee within the given period."""
        if not employee:
            return 0.0
        sql_query = f"""SELECT COALESCE(SUM(validated_overtime_hours), 0.0)
            FROM hr_attendance
            WHERE employee_id = {employee} AND
            (check_in::DATE, check_out::DATE) OVERLAPS (DATE '{date_from}', DATE '{date_to}')
        """
        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchone()
        return round(result[0]) if result else 0.0