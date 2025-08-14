from odoo import models
from datetime import datetime

class WeeklySalesReport(models.AbstractModel):
    _name = 'report.salesman_ageing_report.ageing_report'
    _description = 'Salesman Ageing Report'
    _inherit = "report.report_xlsx.abstract"

    def get_ageing_report_lines(self, data, workbook):
        date_from = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
        target_move = data.get('target_move')
        salesman_ids = data.get('salesman_ids')
        sheet = workbook.add_worksheet('Salesman Ageing Report')

        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'font_color': 'black', 
            'bg_color': '#A0D683', 'border': 1
        })
        salesman_format = workbook.add_format({
            'bold': True, 'align': 'center', 'font_color': 'white', 
            'bg_color': '#5F9EA0', 'border': 1
        })
        text_format = workbook.add_format({
            'align': 'left', 'border': 1
        })
        data_format = workbook.add_format({
            'align': 'right', 'border': 1, 'num_format': '#,##0.00'
        })
        overdue_day_format = workbook.add_format({
            'align': 'right', 'border': 1
        })
        total_number_format = workbook.add_format({
            'bold': True, 'font_color': 'black', 'bg_color': '#D3D3D3', 
            'align': 'right', 'border': 1, 'num_format': '#,##0.00'
        })
        grand_total_format = workbook.add_format({
            'bold': True, 'align': 'center', 'font_color': 'black', 
            'bg_color': '#D3D3D3', 'border': 1
        })

        column_width = 25
        sheet.set_column(0, 1, column_width)
        sheet.set_column(2, 4, column_width)
        sheet.set_column(5, 6, column_width)

        sheet.write(0, 0, 'Date From:', header_format)
        sheet.write(0, 1, date_from.strftime('%Y-%m-%d'), text_format)
        sheet.write(1, 0, 'Target Move:', header_format)
        sheet.write(1, 1, 'Posted Entries' if target_move == 'posted' else 'All Entries', text_format)

        salesman_names = ', '.join(
            self.env['res.users'].browse(salesman_ids).mapped('name')
        ) if salesman_ids else 'All'
        sheet.write(2, 0, 'Salesmans:', header_format)
        sheet.write(2, 1, salesman_names, text_format)
        row = 4  

        invoice_state = ['posted'] if target_move == 'posted' else ['draft', 'posted']
        domain = [('invoice_date_due', '<=', date_from), ('state', 'in', invoice_state)]
        if salesman_ids:
            domain.append(('invoice_user_id', 'in', salesman_ids))
        invoices = self.env['account.move'].search(domain)

        grouped_data = {}
        for inv in invoices:
            salesman = inv.invoice_user_id
            if not salesman:
                continue
            if salesman not in grouped_data:
                grouped_data[salesman] = []
            grouped_data[salesman].append(inv)

        for salesman, invs in grouped_data.items():
            sheet.merge_range(row, 0, row, 6, f'Salesman: {salesman.name}', salesman_format)
            row += 1

            sheet.write(row, 0, 'Customer Name', header_format)
            sheet.write(row, 1, 'Location', header_format)
            sheet.write(row, 2, '0-5 Days', header_format)
            sheet.write(row, 3, '6-15 Days', header_format)
            sheet.write(row, 4, '15-1000 Days', header_format)
            sheet.write(row, 5, 'Total Outstanding', header_format)
            sheet.write(row, 6, 'Overdue Days', header_format)
            row += 1

            customer_data = {}
            for inv in invs:
                customer = inv.partner_id
                overdue_days = (date_from - inv.invoice_date_due).days if inv.invoice_date_due else 0
                ageing = (
                    '0-5 Days' if 0 <= overdue_days <= 5 else
                    '6-15 Days' if 6 <= overdue_days <= 15 else
                    '15-1000 Days'
                )

                # Initialize customer data
                if customer not in customer_data:
                    customer_data[customer] = {
                        'location': customer.city or '',
                        '0-5 Days': 0.0,
                        '6-15 Days': 0.0,
                        '15-1000 Days': 0.0,
                        'total_outstanding': 0.0,
                        'overdue_days': 0,
                    }

                # Update customer data
                customer_data[customer][ageing] += inv.amount_residual
                customer_data[customer]['total_outstanding'] += inv.amount_residual
                customer_data[customer]['overdue_days'] = max(customer_data[customer]['overdue_days'], overdue_days)

            for customer, data in customer_data.items():
                sheet.write(row, 0, customer.name, text_format)
                sheet.write(row, 1, data['location'], text_format)
                sheet.write(row, 2, data['0-5 Days'], data_format)
                sheet.write(row, 3, data['6-15 Days'], data_format)
                sheet.write(row, 4, data['15-1000 Days'], data_format)
                sheet.write(row, 5, data['total_outstanding'], data_format)
                sheet.write(row, 6, data['overdue_days'], overdue_day_format)
                row += 1

            sheet.write(row, 0, 'Grand Total', grand_total_format)
            sheet.write(row, 2, sum(data['0-5 Days'] for data in customer_data.values()), total_number_format)
            sheet.write(row, 3, sum(data['6-15 Days'] for data in customer_data.values()), total_number_format)
            sheet.write(row, 4, sum(data['15-1000 Days'] for data in customer_data.values()), total_number_format)
            sheet.write(row, 5, sum(data['total_outstanding'] for data in customer_data.values()), total_number_format)
            row += 2

    def generate_xlsx_report(self, workbook, data, objs):
        self.get_ageing_report_lines(data, workbook)
