import xlsxwriter
from odoo import models


class OfferSalesReport(models.AbstractModel):
    _name = 'report.offer_sales_report.offer_sales'
    _description = 'Offer Sales Excel Report'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        month_display = data.get('month', '')
        year = data.get('year', '')
        report_data = data.get('sales_data', [])

        sheet = workbook.add_worksheet(f"Offer Sales {month_display} {year}")
        
        bold = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#c0e1d6', 'border': 1})
        cell_format = workbook.add_format({'align': 'left', 'border': 1})
        currency_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'border': 1})
        numeric_format = workbook.add_format({'align': 'right', 'border': 1})

        sheet.merge_range('A1:F1', f"Offer Sales Report - {month_display} {year}", bold)

        headers = ['Date', 'Product', 'Salesman', 'Total Sales Amount', 'Total Profit', 'Units Sold']
        for col_num, header in enumerate(headers):
            sheet.write(2, col_num, header, bold)

        row = 3
        for entry in report_data:
            sheet.write(row, 0, entry.get('date', ''), cell_format)  # Date
            sheet.write(row, 1, entry.get('product', ''), cell_format)  # Product
            sheet.write(row, 2, entry.get('salesman', ''), cell_format)  # Salesman
            sheet.write(row, 3, entry.get('total_sales_amount', 0), currency_format)  # Total Sales Amount
            sheet.write(row, 4, entry.get('total_profit', 0), currency_format)  # Total Profit
            sheet.write(row, 5, entry.get('units_sold', 0), numeric_format)  # Units Sold
            row += 1

        sheet.set_column(0, 0, 15)  # Date
        sheet.set_column(1, 1, 25)  # Product
        sheet.set_column(2, 2, 20)  # Salesman
        sheet.set_column(3, 4, 20)  # Total Sales Amount / Total Profit
        sheet.set_column(5, 5, 15)  # Units Sold