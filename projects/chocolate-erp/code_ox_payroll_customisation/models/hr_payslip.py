from odoo import _, api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(HrPayslip, self).get_inputs(contracts, date_from, date_to)
        other_allowances = self._get_other_allowances(contracts.employee_id.id, date_from,date_to)
        allowance_category = self.env['hr.salary.rule.category'].search(
                [('code', '=', 'ALW')], limit=1
            )
        if not allowance_category:
            allowance_category = self.env['hr.salary.rule.category'].create({
                'name': 'Allowance',
                'code': 'ALW',
            })
        for allowance in other_allowances:
            rule = self.env['hr.salary.rule'].search(
                [('code', '=', allowance['code'])], limit=1
            )
            if not rule:
                amount_python_compute = 'result = inputs.%s.amount\nresult_name = inputs.%s.name' % (allowance['code'], allowance['code'])
                condition_python = 'result = inputs.%s' % allowance['code']
                rule = self.env['hr.salary.rule'].create({
                    'name': allowance['name'],
                    'code': allowance['code'],
                    'category_id': allowance_category.id,
                    'sequence': 10,
                    'condition_select': 'python',
                    'condition_python': condition_python,
                    'amount_select': 'code',
                    'amount_python_compute': amount_python_compute,
                    'appears_on_payslip': True,
                    'is_other_allowance': True,
                })
            if self.struct_id and rule not in self.struct_id.rule_ids:
                self.struct_id.write({'rule_ids': [(4, rule.id)]})
            line_exists = self.input_line_ids.filtered(lambda l: l.code == allowance['code'])
            if line_exists:
                line_exists.amount = allowance['amount']
            allowance_line = {
                'name': allowance['name'],
                'code': allowance['code'],
                'amount': allowance['amount'],
                'contract_id': contracts.id,
            }
            res += [allowance_line]
        return res

    def _get_other_allowances(self, employee, date_from, date_to):
        if not employee:
            return []
        other_allowances = self.env['employee.other.allowance'].search([
            ('employee_id', '=', employee),
            ('state', '=', 'confirm'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ])
        return [{'name': allowance.allowance_type_id.name, 'code': allowance.allowance_type_id.code, 'amount': allowance.amount} for allowance in other_allowances]