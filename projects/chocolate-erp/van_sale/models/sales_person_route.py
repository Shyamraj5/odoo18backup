from odoo import api,fields,models


class Routes(models.Model):
    _name = "route.route"


    name = fields.Char(string='Name')
    shops_ids = fields.One2many('res.partner',string='Shop',inverse_name='route_id')




class ResPartner(models.Model):
    _inherit = "res.partner"

    route_id = fields.Many2one('route.route')
