from odoo import models, fields
from io import BytesIO
import xlsxwriter
import base64

class ExpiryStockReport(models.AbstractModel):
    _name = 'report.inventory_stock_report.expiry_stock_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        to_be_expired = data['to_be_expired']
        expired = data['expired']
        as_on_date = data['as_on_date']

        worksheet = workbook.add_worksheet('Expiry Stock Report')

        # Formats
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'left'})
        subheader_format = workbook.add_format({'align': 'left', 'font_color': 'black', 'bg_color': '#FFFF00'})
        header_format = workbook.add_format({ 'align': 'center', 'font_color': 'black', 'border': 1})
        section_title_format = workbook.add_format({'bold': False, 'font_color': 'black', 'align': 'left'})
        bold_format = workbook.add_format({'bold': False, 'border': 1,'font_color':'red'})
        normal_format = workbook.add_format({'border': 1})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1})
        currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        total_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1,'bold':True})
        percentage_format = workbook.add_format({'num_format': '0.00%', 'border': 1})
        # Report Title and As on Date
        worksheet.merge_range('A1:M1', 'Expiry Stock Report', title_format)
        worksheet.write('A2', 'As on Date:', bold_format)
        worksheet.write('B2', as_on_date, date_format)

        # Headers
        headers = [
            'Purchase Date', 'Product', 'Purchase Supplier', 'Purchase Quantity', 
            'Lot No', 'Quantity', 'UoM', 'Unit Cost', 'Stock Value', 
            'Expiry Date', 'No of days left', 'Left Over %', 'Location'
        ]
        worksheet.write_row('A4', headers, header_format)

        # "To Be Expired" Section
        row = 5
        worksheet.merge_range(f'A{row}:M{row}', 'To be expired', section_title_format)
        row += 1
        total_to_be_expired = 0
        total_quantity = 0

        for item in to_be_expired:
            worksheet.write(row, 0, item['purchase_date'], date_format)
            worksheet.write(row, 1, item['product'], normal_format)
            worksheet.write(row, 2, item.get('vendor', ''), normal_format)  # Add purchase supplier if applicable
            worksheet.write(row, 3, item['purchase_quantity'], normal_format)
            worksheet.write(row, 4, item['lot_no'], normal_format)
            worksheet.write(row, 5, item['quantity'], normal_format)
            worksheet.write(row, 6, item['uom'], normal_format)
            worksheet.write(row, 7,item['cost'], currency_format)
            worksheet.write(row, 8, item['stock_value'], currency_format)
            worksheet.write(row, 9, item['expiry_date'], date_format)
            worksheet.write(row, 10, item['days_left'], normal_format)
            leftover_percentage =  item['quantity'] / item['purchase_quantity'] if item['purchase_quantity'] else 0
            worksheet.write(row, 11, leftover_percentage, percentage_format)
            worksheet.write(row, 12, item['location'], normal_format)
            total_to_be_expired += item['stock_value']
            total_quantity += item['quantity']
            row += 1

        worksheet.write(row, 8, total_to_be_expired, total_format)
        worksheet.write(row,5,total_quantity,total_format)
        row += 2

        # "Expired" Section
        worksheet.merge_range(f'A{row}:M{row}', 'Expired', section_title_format)
        row += 1
        total_expired = 0
        total_exp_quantity=0
        for item in expired:
            worksheet.write(row, 0, item['purchase_date'], date_format)
            worksheet.write(row, 1, item['product'], normal_format)
            worksheet.write(row, 2, item.get('vendor', ''), normal_format)  # Add purchase supplier if applicable
            worksheet.write(row, 3, item['purchase_quantity'], normal_format)
            worksheet.write(row, 4, item['lot_no'], normal_format)
            worksheet.write(row, 5, item['quantity'], normal_format)
            worksheet.write(row, 6, item['uom'], normal_format)
            worksheet.write(row, 7,item['cost'], currency_format)
            worksheet.write(row, 8, item['stock_value'], currency_format)
            worksheet.write(row, 9, item['expiry_date'], date_format)
            worksheet.write(row, 10, item[('days_left')], normal_format)
            leftover_percentage = item['quantity'] / item['purchase_quantity'] if item['purchase_quantity'] else 0
            worksheet.write(row, 11, leftover_percentage, percentage_format)
            worksheet.write(row, 12, item['location'], normal_format)
            total_exp_quantity += item['quantity']
            total_expired += item['stock_value']
            row += 1

        worksheet.write(row, 8, total_expired, total_format)
        worksheet.write(row,5,total_exp_quantity,total_format)

        # Adjust column widths for better alignment
        column_widths = [15, 20, 20, 18, 15, 10, 10, 10, 15, 15, 15, 15, 20]
        for i, width in enumerate(column_widths):
            worksheet.set_column(i, i, width)