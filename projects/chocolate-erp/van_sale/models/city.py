from odoo import models, fields


class ResContryStateCity(models.Model):
    _name = 'res.country.state.city'
    _description = 'City'

    name = fields.Char(string="City Name")
