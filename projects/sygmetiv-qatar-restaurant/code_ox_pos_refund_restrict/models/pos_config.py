from odoo import fields, models, api


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    restrict_refund = fields.Boolean("Restrict Refund")
