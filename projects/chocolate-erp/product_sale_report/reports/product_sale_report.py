from odoo import models
import xlsxwriter
import base64
from io import BytesIO

class SaleXlsxReport(models.AbstractModel):
    _name = 'report.product_sale_report.sale_xlsx_report'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Sale XLSX Report'

    def generate_xlsx_report(self, workbook, data, wizard):
        report_data = data.get('report_data', [])
        totals = data.get('totals', {})
        worksheet = workbook.add_worksheet('Sale Report')

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_color': '#FF0000'
        })
        
        total_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'bg_color': '#FFE699'
        })

        headers = ['Date', 'Ref No', 'Vendor Name', 'Product Code', 'Batch Code', 
                'Product Name', 'Quantity', 'UoM', 'Unit Price', 'Gross', 
                'Discount', 'VAT','Net Amount', 'Cost', 'Profit']
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        for row, line in enumerate(report_data, 1):
            worksheet.write(row, 0, line['date'])
            worksheet.write(row, 1, line['invoice_number'])
            worksheet.write(row, 2, line['partner_name'])
            worksheet.write(row, 3, line['product_code'])
            worksheet.write(row, 4, line['batch_code'])
            worksheet.write(row, 5, line['product_name'])
            worksheet.write(row, 6, line['quantity'])
            worksheet.write(row, 7, line['uom'])
            worksheet.write(row, 8, line['unit_price'])
            worksheet.write(row, 9, line['gross'])
            worksheet.write(row, 10, line['discount'])
            worksheet.write(row, 11, line['vat'])
            worksheet.write(row, 12, line['net_amount'])
            worksheet.write(row, 13, line['cost'])
            worksheet.write(row, 14, line['margin'])

        total_row = len(report_data) + 2  
        worksheet.write(total_row, 5, 'Total', total_format)
        worksheet.write(total_row, 6, totals['total_quantity'], total_format)
        worksheet.write(total_row, 8, totals['total_unit_price'], total_format)
        worksheet.write(total_row, 9, totals['total_gross'], total_format)
        worksheet.write(total_row, 10, totals['total_discount'], total_format)
        worksheet.write(total_row, 11, totals['total_vat'], total_format)
        worksheet.write(total_row, 12, totals['total_net'], total_format)
        worksheet.write(total_row, 14, totals['total_margin'], total_format)

        for i, header in enumerate(headers):
            base_width = len(header) + 5
            if i == 0:
                worksheet.set_column(i, i, base_width * 1.25)  
            elif i == 1:
                worksheet.set_column(i, i, base_width * 1.50)
            else:
                worksheet.set_column(i, i, base_width)