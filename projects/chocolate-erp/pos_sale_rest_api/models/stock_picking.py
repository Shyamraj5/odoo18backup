from odoo import models, fields,api



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    delivery_priority_id = fields.Many2one('delivery.priority', string='Delivery Priority')
    delivery_description = fields.Text(string='Delivery Description')

    
