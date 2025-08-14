from odoo import http
from odoo.http import request

class PublicCompanyController(http.Controller):
    @http.route('/public/company_data', type='json', auth="public")
    def get_public_company_data(self):
        companies = request.env['res.company'].sudo().search_read([], ['name', 'id'])
        return companies
