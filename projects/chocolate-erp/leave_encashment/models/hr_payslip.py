from odoo import _, api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        leave_encashment_amount = self._get_leave_encashment_amount(contracts.employee_id.id, date_from,date_to)
        allowance_category = self.env['hr.salary.rule.category'].search(
                [('code', '=', 'ALW')], limit=1
            )
        if not allowance_category:
            allowance_category = self.env['hr.salary.rule.category'].create({
                'name': 'Allowance',
                'code': 'ALW',
            })
        encashment_rule = self.env['hr.salary.rule'].search(
            [('code', '=', 'LEAVE_ENC')], limit=1
        )
        if not encashment_rule:
            amount_python_compute = 'result = inputs.LEAVE_ENC.amount\nresult_name = inputs.LEAVE_ENC.name'
            condition_python = 'result = inputs.LEAVE_ENC'
            encashment_rule = self.env['hr.salary.rule'].create({
                'name': 'Leave Encashment',
                'code': 'LEAVE_ENC',
                'category_id': allowance_category.id,
                'sequence': 10,
                'condition_select': 'python',
                'condition_python': condition_python,
                'amount_select': 'code',
                'amount_python_compute': amount_python_compute,
                'appears_on_payslip': True,
            })
        
        if leave_encashment_amount > 0:
            if self.struct_id and encashment_rule not in self.struct_id.rule_ids:
                self.struct_id.write({'rule_ids': [(4, encashment_rule.id)]})
            line_exists = self.input_line_ids.filtered(lambda l: l.code == 'LEAVE_ENC')
            if line_exists:
                line_exists.amount = leave_encashment_amount
            encashment_line = {
                'name': 'Leave Encashment',
                'code': 'LEAVE_ENC',
                'amount': leave_encashment_amount,
                'contract_id': contracts.id,
            }
            res += [encashment_line]
        return res

    def _get_leave_encashment_amount(self, employee, date_from, date_to):
        """Fetch the total leave encashment amount for the employee within the given period."""
        if not employee:
            return 0.0
        leave_encashments = self.env['leave.encashment'].search([
            ('employee_id', '=', employee),
            ('state', '=', 'approved'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])
        return sum(encashment.amount for encashment in leave_encashments)