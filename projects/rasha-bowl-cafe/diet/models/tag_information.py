from odoo import models, fields
from datetime import date

class TagInformation(models.Model):
    _name = 'tag.information'
    _description = "Tag information"
    
    tag = fields.Char(string='Tag')
    type = fields.Char(string='type')
    start_date =fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    product_id = fields.Many2one('product.product', string='Product')