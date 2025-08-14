from odoo import models
from datetime import datetime
from collections import defaultdict

class WeeklySalesReport(models.AbstractModel):
    _name = 'report.location_report.location_report'
    _description = 'Location Report'
    _inherit = "report.report_xlsx.abstract"

    def get_location_report_lines(self, data, workbook):
        date_from = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
        target_move = data.get('target_move')
        route_location_ids = data.get('route_location_ids')
        sheet = workbook.add_worksheet('Location Report')

        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'font_color': 'black',
            'bg_color': '#A0D683', 'border': 1
        })
        text_format = workbook.add_format({'align': 'left', 'border': 1})
        data_format = workbook.add_format({'align': 'right', 'border': 1, 'num_format': '#,##0.00'})
        overdue_day_format = workbook.add_format({'align': 'right', 'border': 1})
        total_number_format = workbook.add_format({
            'bold': True, 'font_color': 'black', 'bg_color': '#D3D3D3',
            'align': 'right', 'border': 1, 'num_format': '#,##0.00'
        })
        grand_total_format = workbook.add_format({
            'bold': True, 'align': 'center', 'font_color': 'black',
            'bg_color': '#D3D3D3', 'border': 1
        })
        route_format = workbook.add_format({
            'bold': True, 'font_color': 'black',
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        city_format = workbook.add_format({
            'bold': True, 'font_color': 'black',
            'align': 'center', 'valign': 'vcenter', 'border': 1,
            'bg_color': '#F0F0F0'
        })

        column_width = 25
        sheet.set_column(0, 7, column_width)
        sheet.write(0, 0, 'Date From:', header_format)
        sheet.write(0, 1, date_from.strftime('%Y-%m-%d'), text_format)
        sheet.write(1, 0, 'Target Move:', header_format)
        sheet.write(1, 1, 'Posted Entries' if target_move == 'posted' else 'All Entries', text_format)

        invoice_state = ['posted'] if target_move == 'posted' else ['draft', 'posted']
        domain = [('invoice_date_due', '<=', date_from), ('state', 'in', invoice_state)]

        if route_location_ids:
            domain.append(('partner_id.route_id', 'in', route_location_ids))

        invoices = self.env['account.move'].search(domain)
        city_data = defaultdict(lambda: defaultdict(dict))
        
        for inv in invoices:
            customer = inv.partner_id
            if not customer or not customer.name or not customer.country_city_id:
                continue
            route = customer.route_id
            route_name = route.name if route else 'No Routes Assigned'
            city = customer.country_city_id.name
            overdue_days = (date_from - inv.invoice_date_due).days if inv.invoice_date_due else 0
            ageing = (
                '0-5 Days' if 0 <= overdue_days <= 5 else
                '6-15 Days' if 6 <= overdue_days <= 15 else
                '15-1000 Days'
            )

            if customer not in city_data[city][route_name]:
                city_data[city][route_name][customer] = {
                    '0-5 Days': 0.0,
                    '6-15 Days': 0.0,
                    '15-1000 Days': 0.0,
                    'total_outstanding': 0.0,
                    'overdue_days': 0,
                }

            city_data[city][route_name][customer][ageing] += inv.amount_residual
            city_data[city][route_name][customer]['total_outstanding'] += inv.amount_residual
            city_data[city][route_name][customer]['overdue_days'] = max(
                city_data[city][route_name][customer]['overdue_days'], overdue_days
            )

        row = 4
        sheet.write(row, 0, 'City', header_format)
        sheet.write(row, 1, 'Routes Location', header_format)
        sheet.write(row, 2, 'Customer Name', header_format)
        sheet.write(row, 3, '0-5 Days', header_format)
        sheet.write(row, 4, '6-15 Days', header_format)
        sheet.write(row, 5, '15-1000 Days', header_format)
        sheet.write(row, 6, 'Total Outstanding', header_format)
        sheet.write(row, 7, 'Overdue Days', header_format)
        row += 1

        for city, routes in sorted(city_data.items()):
            city_row_start = row
            total_customers_in_city = sum(len(customers) for customers in routes.values())

            for route_name, customers in sorted(routes.items()):
                route_row_start = row

                for customer, data in sorted(customers.items(), key=lambda x: x[0].name):
                    sheet.write(row, 2, customer.name, text_format)
                    sheet.write(row, 3, data['0-5 Days'], data_format)
                    sheet.write(row, 4, data['6-15 Days'], data_format)
                    sheet.write(row, 5, data['15-1000 Days'], data_format)
                    sheet.write(row, 6, data['total_outstanding'], data_format)
                    sheet.write(row, 7, data['overdue_days'], overdue_day_format)
                    row += 1

                if route_row_start < row - 1:
                    sheet.merge_range(route_row_start, 1, row - 1, 1, route_name, route_format)
                elif route_row_start == row - 1:
                    sheet.write(route_row_start, 1, route_name, route_format)

            if total_customers_in_city > 1:
                sheet.merge_range(city_row_start, 0, row - 1, 0, city, city_format)
            else:
                sheet.write(city_row_start, 0, city, city_format)

            sheet.write(row, 0, f'Total for {city}', grand_total_format)
            city_total_0_5 = sum(sum(data['0-5 Days'] for data in customers.values()) for customers in routes.values())
            city_total_6_15 = sum(sum(data['6-15 Days'] for data in customers.values()) for customers in routes.values())
            city_total_15_1000 = sum(sum(data['15-1000 Days'] for data in customers.values()) for customers in routes.values())
            city_total_outstanding = sum(sum(data['total_outstanding'] for data in customers.values()) for customers in routes.values())
            
            sheet.write(row, 3, city_total_0_5, total_number_format)
            sheet.write(row, 4, city_total_6_15, total_number_format)
            sheet.write(row, 5, city_total_15_1000, total_number_format)
            sheet.write(row, 6, city_total_outstanding, total_number_format)
            row += 2

    def generate_xlsx_report(self, workbook, data, objs):
        self.get_location_report_lines(data, workbook)