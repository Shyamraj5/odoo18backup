from odoo import models, fields, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    mobile_allowance = fields.Monetary(string="Mobile Allowance", help="Mobile allowances")
