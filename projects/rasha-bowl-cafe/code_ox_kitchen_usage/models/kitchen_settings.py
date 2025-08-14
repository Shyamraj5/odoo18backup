from odoo import models, fields, api


class Resconfig(models.TransientModel):
    _inherit = 'res.config.settings'
 
    location_id = fields.Many2one('stock.location', string="Source Location" ,config_parameter="code_ox_kitchen_usage.location_id")
    location_dest_id = fields.Many2one('stock.location', string="Destination Location", config_parameter="code_ox_kitchen_usage.location_dest_id")


    source_location = fields.Many2one('stock.location', string="Source Location" ,config_parameter="code_ox_kitchen_usage.source_location")
