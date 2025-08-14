from odoo import models, fields

class RoundOffBoolean(models.Model):
    _inherit = "product.template"

    is_roundoff = fields.Boolean(string="Apply Round Off", default=False)