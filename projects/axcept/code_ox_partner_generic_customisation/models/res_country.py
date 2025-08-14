from odoo import models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    show_in_app = fields.Boolean(default=False)