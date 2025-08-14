from odoo import models, fields

class ResCountryState(models.Model):
    _inherit = 'res.country.state'
    _description = 'Res Country State'
    
    active = fields.Boolean('Active', default=True)
