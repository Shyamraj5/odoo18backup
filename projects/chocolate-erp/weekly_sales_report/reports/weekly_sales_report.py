from odoo import models
import xlsxwriter
from datetime import datetime, timedelta
import calendar

class WeeklySalesReport(models.AbstractModel):
    _name = 'report.weekly_sales_report.sales_report'
    _description = 'Sales Excel Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        start_date = datetime.strptime(data.get('start_date'), "%Y-%m-%d").date()
        end_date = datetime.strptime(data.get('end_date'), "%Y-%m-%d").date()
        sheet = workbook.add_worksheet('Sales Report')

        header_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#72BF78',
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        date_header_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#A0D683',
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        salesperson_format = workbook.add_format({
            'bold': True, 
            'bg_color': '#5F9EA0',
            'font_color': 'white',
            'align': 'center',
            'border': 1
        })

        number_format = workbook.add_format({
            'num_format': '#,##0.00', 
            'align': 'right',
            'border': 1
        })

        date_format = workbook.add_format({
            'align': 'left',
            'border': 1
        })

        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3EE98',
            'font_color': 'black',
            'align': 'center',
            'border': 1
        })

        total_number_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',
            'align': 'right',
            'border': 1,
            'bg_color': '#D0E8C5',
            'font_color': 'black'
        })

        domain = [
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('invoice_ids.state', '=', 'posted'),
        ]
        sale_orders = self.env['sale.order'].search(domain)

        sale_types = {
            'B2B': 'b2b',
            'Van Sale': 'vansale',
            'Wholesale': 'wholesale'
        }
        sales_data = {}
        for display_name, sale_type in sale_types.items():
            type_orders = sale_orders.filtered(lambda o: o.sale_type == sale_type)
            salespeople = type_orders.mapped('user_id')
            if salespeople:
                sales_data[display_name] = list(set(salespeople))
        sheet.merge_range('A1:A2', 'Date', date_header_format)
        sheet.merge_range('B1:B2', 'Month', date_header_format)
        sheet.merge_range('C1:C2', 'Day', date_header_format)

        col_index = 3
        for sale_type, salespeople in sales_data.items():
            if salespeople:
                if len(salespeople) == 1:
                    sheet.write(0, col_index, sale_type, header_format)
                else:
                    sheet.merge_range(0, col_index, 0, col_index + len(salespeople) - 1, sale_type, header_format)
                col_index += len(salespeople)

        salesperson_columns = {}
        col_index = 3
        for sale_type, salespeople in sales_data.items():
            for salesperson in salespeople:
                sheet.write(1, col_index, salesperson.name, salesperson_format)
                salesperson_columns[(sale_type, salesperson.id)] = col_index
                col_index += 1

        displayed_totals = {col: 0 for col in range(3, col_index)}
        
        row = 2
        current_date = start_date
        while current_date <= end_date:
            sheet.write(row, 0, str(current_date), date_format)
            sheet.write(row, 1, calendar.month_name[current_date.month], date_format)
            sheet.write(row, 2, calendar.day_name[current_date.weekday()], date_format)

            daily_orders = sale_orders.filtered(
                lambda o: o.date_order.date() == current_date
            )

            for display_name, sale_type in sale_types.items():
                type_orders = daily_orders.filtered(lambda o: o.sale_type == sale_type)

                for salesperson in sales_data.get(display_name, []):
                    salesperson_orders = type_orders.filtered(lambda o: o.user_id.id == salesperson.id)
                    total_amount = sum(
                        invoice.amount_total
                        for order in salesperson_orders
                        for invoice in order.invoice_ids.filtered(lambda i: i.state == 'posted')
                    )
                    
                    col = salesperson_columns.get((display_name, salesperson.id))
                    if col is not None:
                        sheet.write(row, col, total_amount, number_format)
                        displayed_totals[col] += total_amount

            row += 1
            current_date += timedelta(days=1)

        sheet.merge_range(row, 0, row, 2, 'Grand Total', total_format)

        for col in range(3, col_index):
            sheet.write(row, col, displayed_totals[col], total_number_format)

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, col_index, 20)
