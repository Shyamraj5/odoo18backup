from odoo import fields, models


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    show_in_app = fields.Boolean(default=False)