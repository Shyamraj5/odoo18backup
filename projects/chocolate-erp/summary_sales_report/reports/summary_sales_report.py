from odoo import models
import xlsxwriter
from datetime import datetime, timedelta
import calendar

class SummarySalesReport(models.AbstractModel):
    _name = 'report.summary_sales_report.sales_report'
    _description = 'Sales Excel Report'
    _inherit = "report.report_xlsx.abstract"


    def generate_xlsx_report(self, workbook, data, lines):
        month_display = data.get('month_display')
        year = data.get('year')
        report_data = data.get('report_data')

        sheet = workbook.add_worksheet(f"Summary {month_display} {year}")
        bold = workbook.add_format({'bold': False, 'align': 'left','bg_color': '#F3F2F2','border': 1,'border_color': '#D0CFCF'})
        currency_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        percentage_format = workbook.add_format({'num_format': '0.00%', 'align': 'right'})
        second_heading = workbook.add_format({'bold': False, 'align': 'center','bg_color': '#D3D3D3'})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#A0D683'})

        sheet.merge_range('A1:D1', f"Sales Summary - {month_display} {year}", heading_format)

        sheet.write(2, 0, "", second_heading)
        salespersons = [entry['salesperson_name'] for entry in report_data]
        for col, salesperson in enumerate(salespersons, start=1):
            sheet.write(2, col, salesperson, second_heading)

        metrics = [
            ('Sales Target', 'target'),
            ('Total Sales', 'achieved'),
            ('Difference', lambda entry: entry['target'] - entry['achieved']),
            ('Avg Daily Sales Required', lambda entry: entry['target'] / 26 if entry['target'] else 0),
            ('Avg Actual Daily Sales', lambda entry: entry['achieved'] / 26),
            ('Target Achieved %', lambda entry: (entry['achieved'] / entry['target']) if entry['target'] else 0),
            ('Total Outstanding', 'amount_residual'),
            ('Gross Profit', 'gross_profit'),
            ('Gross Profit %', lambda entry: entry['gross_profit_percentage'] / 100),  # Already calculated
            ('Avg Daily Gross Profit', 'avg_gross_profit'),  # Already calculated
        ]

        for row, (metric_name, metric_key_or_func) in enumerate(metrics, start=3):
            sheet.write(row, 0, metric_name, bold)

            for col, entry in enumerate(report_data, start=1):
                if callable(metric_key_or_func):
                    value = metric_key_or_func(entry)
                else:
                    value = entry.get(metric_key_or_func, 0)

                if 'Profit' in metric_name or 'Sales' in metric_name or 'Outstanding' in metric_name:
                    fmt = currency_format
                elif '%' in metric_name:
                    fmt = percentage_format
                else:
                    fmt = None

                sheet.write(row, col, value, fmt)

        sheet.set_column('A:A', 30)  # Metrics column
        for col in range(1, len(salespersons) + 1):
            sheet.set_column(col, col, 20)  # Salesperson columns
