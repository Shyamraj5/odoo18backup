from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    customer_type = fields.Selection([('walk_in_customer', 'Outside'), ('hotel_customer', 'Room Guest'), 
                                      ('complementary_customer', 'Complementary Customer')], default='walk_in_customer')
    pos_order_type_id = fields.Many2one('pos.order.type', 'Order Type')
    pos_order_type_text = fields.Char('Order Type Text')
    room_number = fields.Char('Room Number')