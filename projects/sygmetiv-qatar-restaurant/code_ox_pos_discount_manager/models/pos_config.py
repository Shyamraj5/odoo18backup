from odoo import fields, models, api


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    enable_discount_validation = fields.Boolean("Enable Discount Validation for Order")
    discount_limit = fields.Float(string="Discount Limit")
