from odoo import http
from odoo.http import request


class PosController(http.Controller):
    @http.route('/pos/pos_order_type', auth='public', type='json')
    def get_pos_order_types(self):
        order_types = request.env['pos.order.type'].sudo().search([])
        return [{'id': order_type.id, 'name': order_type.name} for order_type in order_types]
    
    @http.route('/pos/pos_order_type_name/<id>', auth='public', type='json')
    def get_pos_order_type_name(self, id):
        order_type = request.env['pos.order.type'].sudo().browse([int(id)])
        return {'id': order_type.id, 'name': order_type.name}
    
    
    
