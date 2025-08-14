from odoo import fields, models


class ResDistrict(models.Model):
    _name = 'res.district'
    _description = 'District Master'

    name = fields.Char(string='Name')
    country_id = fields.Many2one(comodel_name='res.country', string='Country', required=True)
    state_id = fields.Many2one(comodel_name='res.country.state', string='State', domain="[('country_id', '=', country_id)]")
