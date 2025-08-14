import calendar
from odoo import models, fields
from datetime import date, datetime, timedelta



MONTHS = [
    ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
]
YEARS = [(str(year), str(year)) for year in range(2020, 2050)]

class SummarySalesWizard(models.TransientModel):
    _name = 'summary.sales.wizard'
    _description = 'summary Sales Wizard'

    month = fields.Selection(
        selection=MONTHS,
        string='Month',
        default=lambda self: str(datetime.now().month),
    )
    year = fields.Selection(
        selection=YEARS,
        string='Year',
        default=lambda self: str(datetime.now().year),
    )
    def generate_excel_report(self):
        self.ensure_one()
        month = self.month
        year = self.year
        start_date = f'{year}-{month}-01'
        end_date = f'{year}-{month}-{calendar.monthrange(int(year), int(month))[1]}'
        month_display = dict(self._fields['month'].selection).get(month)

        # Fetch target data
        target_lines = self.env['salesperson.target.line'].search([
            ('commission_plan_salesperson_id.commission_plan_id.effective_period_start', '<=', start_date),
            ('commission_plan_salesperson_id.commission_plan_id.effective_period_end', '>=', start_date),
        ])

        # Aggregate target and achieved data
        report_data = {}
        for line in target_lines:
            salesperson = line.commission_plan_salesperson_id.salesperson_id
            if salesperson.id not in report_data:
                report_data[salesperson.id] = {
                    'salesperson_name': salesperson.name,
                    'target': 0,
                    'achieved': 0,
                    'gross_profit': 0,
                    'amount_residual': 0,
                    'gross_profit_percentage': 0,  
                    'avg_gross_profit': 0, 
                }
            report_data[salesperson.id]['target'] += line.target_amount

        # Fetch achieved sales and calculate additional metrics for each salesperson
        for salesperson_id, values in report_data.items():
            achieved_sales = self.env['sale.order'].search([
                ('user_id', '=', salesperson_id),
                ('date_order', '>=', start_date),
                ('date_order', '<=', end_date),
                ('invoice_status', '=', 'invoiced')
            ]).mapped('amount_total')
            total_achieved_sales = sum(achieved_sales)
            report_data[salesperson_id]['achieved'] = total_achieved_sales

            # Calculate gross profit
            gross_profit = self.env['sale.order.line'].search([
                ('order_id.user_id', '=', salesperson_id),
                ('order_id.date_order', '>=', start_date),
                ('order_id.date_order', '<=', end_date),
                ('order_id.invoice_status', '=', 'invoiced')
            ]).mapped('margin')
            total_gross_profit = sum(gross_profit)
            report_data[salesperson_id]['gross_profit'] = total_gross_profit

            # Calculate gross profit percentage
            if total_achieved_sales > 0:
                report_data[salesperson_id]['gross_profit_percentage'] = (total_gross_profit / total_achieved_sales) * 100

            # Calculate average gross profit
            report_data[salesperson_id]['avg_gross_profit'] = total_gross_profit / 26 if total_gross_profit > 0 else 0

            # Calculate outstanding amount (amount_residual)
            outstanding_invoices = self.env['account.move'].search([
                ('state', '=', 'posted'),
                ('invoice_date', '>=', start_date),
                ('invoice_date', '<=', end_date),
                ('amount_residual', '>', 0),
                ('user_id', '=', salesperson_id)
            ])
            report_data[salesperson_id]['amount_residual'] = sum(invoice.amount_residual for invoice in outstanding_invoices)

        # Prepare data for the report
        data = {
            'month_display': month_display,
            'year': year,
            'report_data': list(report_data.values()),
            'total_outstanding': sum([entry['amount_residual'] for entry in report_data.values()]),
            'total_active_customers': self.env['res.partner'].search_count([('customer_rank', '>', 0), ('active', '=', True)]),
            'new_customers': self.env['res.partner'].search_count([
                ('customer_rank', '>', 0),
                ('create_date', '>=', start_date),
                ('create_date', '<=', end_date)
            ]),
            'total_gross_profit': sum([entry['gross_profit'] for entry in report_data.values()]),
        }

        return self.env.ref('summary_sales_report.action_summary_sales_report').report_action(self, data=data)
