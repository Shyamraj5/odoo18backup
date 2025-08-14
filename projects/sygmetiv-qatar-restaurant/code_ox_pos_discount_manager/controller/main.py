from odoo import http
from odoo.http import request

    
class PoSDiscountController(http.Controller):
    @http.route('/pos/discount_data', type='json', auth='user')
    def get_discount_data(self, data):
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', int(data))])
        return {
            'discount_limit': employee.limited_discount,
            'manager_pin': employee.parent_id.pin if employee.parent_id else ''
        }

    
