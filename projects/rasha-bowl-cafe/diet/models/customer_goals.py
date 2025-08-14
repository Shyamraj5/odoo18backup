from odoo import models, fields

class CustomerGoals(models.Model):
    _name = 'customer.goals'
    _description = 'Customer Goals'

    name = fields.Char(string='Goal Name', required=True)
