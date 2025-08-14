from odoo import http
from odoo.http import request

class VatReportController(http.Controller):

    @http.route('/codeox_vat_report/vat_report_data', type='json', auth='user')
    def get_vat_report_data(self, start_date, end_date):
        try:
            report_model = request.env['report.codeox_vat_report.html_report']
            company = request.httprequest.cookies.get('cids')
            report_data = report_model._get_report_values(docids=None, data={'start_date': start_date, 'end_date': end_date, 'company': company})
            
            return report_data
        except Exception as e:
            return{"error":str(e)}
        