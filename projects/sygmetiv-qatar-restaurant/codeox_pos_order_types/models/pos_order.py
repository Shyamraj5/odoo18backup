from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    pos_order_type_id = fields.Many2one('pos.order.type', 'Order Type')
    pos_order_type_text = fields.Char('Order Type Text')