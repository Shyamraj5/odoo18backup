from odoo import fields, models, api


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    default_order_type_id = fields.Many2one('pos.order.type', string="Order Type")