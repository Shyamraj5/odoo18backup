from odoo import models, fields, api, _


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_other_allowance = fields.Boolean(string='Is Other Allowance', default=False)