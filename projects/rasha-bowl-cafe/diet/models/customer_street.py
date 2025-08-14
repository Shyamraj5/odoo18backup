from odoo import models, fields

class CustomerStreet(models.Model):
    _name = 'customer.street'
    _description = 'Customer Street'
    
    name = fields.Char(string='Name', required=True)
    district_id = fields.Many2one('customer.district', string='Zone', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)