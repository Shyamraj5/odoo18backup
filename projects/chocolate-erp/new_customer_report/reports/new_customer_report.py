from odoo import models
import xlsxwriter
from datetime import datetime
from collections import defaultdict

class WeeklySalesReport(models.AbstractModel):
    _name = 'report.new_customer_report.sales_report'
    _description = 'New Customer Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        start_date = datetime.strptime(data.get('start_date'), "%Y-%m-%d").date()
        end_date = datetime.strptime(data.get('end_date'), "%Y-%m-%d").date()

        sheet = workbook.add_worksheet('New Customer Report')
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})

        headers = [
            'Salesperson', 'Invoice Date', 'Customer Name',
            'Invoice Amount', 'Total Returns', 'Total Receipts', 'Outstanding'
        ]

        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, header_format)
            sheet.set_column(col_num, col_num, len(header) + 2)

        invoices = self.env['account.move'].search([
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice')
        ])

        grouped_data = defaultdict(lambda: defaultdict(lambda: {
            'invoice_date': '',
            'invoice_amount': 0,
            'total_returns': 0,
            'total_receipts': 0,
            'outstanding': 0
        }))

        for invoice in invoices:
            if not invoice.invoice_user_id:
                continue
            previous_invoice = self.env['account.move'].search([
                ('invoice_user_id', '=', invoice.invoice_user_id.id),
                ('partner_id', '=', invoice.partner_id.id),
                ('invoice_date', '<', start_date),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice')
            ])

            if previous_invoice:
                continue
            salesperson = invoice.invoice_user_id.name
            customer = invoice.partner_id.name
            total_returns = sum(
                credit_note.amount_total
                for credit_note in self.env['account.move'].search([
                    ('reversed_entry_id', '=', invoice.id),
                    ('move_type', '=', 'out_refund'),
                    ('state', '=', 'posted')
                ])
            )

            actual_invoice_amount = invoice.amount_total
            total_receipts = invoice.amount_total - invoice.amount_residual - total_returns
            outstanding = invoice.amount_residual

            customer_data = grouped_data[salesperson][customer]
            customer_data['invoice_date'] = invoice.invoice_date.strftime("%Y-%m-%d")
            customer_data['invoice_amount'] += actual_invoice_amount
            customer_data['total_returns'] += total_returns
            customer_data['total_receipts'] += total_receipts if total_receipts > 0 else 0
            customer_data['outstanding'] += outstanding

        row = 1
        last_salesperson = None

        for salesperson in sorted(grouped_data.keys()):
            for customer, data in sorted(grouped_data[salesperson].items()):
                salesperson_to_write = salesperson if salesperson != last_salesperson else ""
                last_salesperson = salesperson

                sheet.write(row, 0, salesperson_to_write)
                sheet.write(row, 1, data['invoice_date'])
                sheet.write(row, 2, customer)
                sheet.write(row, 3, data['invoice_amount'])
                sheet.write(row, 4, data['total_returns'])
                sheet.write(row, 5, data['total_receipts'])
                sheet.write(row, 6, data['outstanding'])
                row += 1