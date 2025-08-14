from odoo import models
from datetime import datetime

class SalesTargetReport(models.AbstractModel):
    _name = 'report.sales_excel_report.sales_target_report'
    _description = 'Sales Excel Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        date_from = datetime.strptime(data.get('date_from'), '%Y-%m-%d').date()
        date_to = datetime.strptime(data.get('date_to'), '%Y-%m-%d').date()

        sheet = workbook.add_worksheet('Incentive Report')

        # styles
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#e8ed87'})
        percentage_heading = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#87e1ed'})
        amount_format = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        percentage_format = workbook.add_format({'align': 'right', 'num_format': '0.00%'})

        sheet.write(0, 0, '', header_format)
        approved_commissions = self.env['commission.plan'].search([('state', '=', 'approved')])
        salesperson_targets = approved_commissions.mapped('salesperson_ids')

        col = 1
        for target in salesperson_targets:
            sheet.write(0, col, target.salesperson_id.name, header_format)
            col += 1

        sheet.write(1, 0, 'Sales Total', header_format)
        sheet.write(2, 0, 'Sales Target', header_format)
        sheet.write(3, 0, 'Percentage %', percentage_heading)
        sheet.write(4, 0, 'Incentive', percentage_heading)

        col = 1
        for target in salesperson_targets:
            target_line = target.target_line_ids.filtered(
                lambda line: line.start_date <= date_to and line.end_date >= date_from
            )
            sales_target = sum(target_line.mapped('target_amount'))

            invoices = self.env['account.move'].search([
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<=', date_to),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice'),
                ('user_id', '=', target.salesperson_id.id),
            ])
            sales_total = sum(invoice.amount_total for invoice in invoices)

            percentage = (sales_total / sales_target * 100) if sales_target > 0 else 0

            incentive = 0
            for incentive_line in approved_commissions.mapped('incentive_ids'):
                if percentage >= incentive_line.target_completion:
                    incentive = incentive_line.commission_amount

            sheet.write(1, col, sales_total, amount_format)
            sheet.write(2, col, sales_target, amount_format)
            sheet.write(3, col, percentage / 100, percentage_format)
            sheet.write(4, col, incentive, amount_format)
            col += 1

        sheet.set_column(0, 0, 25)
        sheet.set_column(1, col, 20)
