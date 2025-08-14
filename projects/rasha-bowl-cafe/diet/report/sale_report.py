from calendar import monthrange
from datetime import date
from odoo import models, api


class DailySalesReport(models.AbstractModel):
    _name = "report.diet.sale_report_template"
    _description = "Sales Report Template"

    @api.model
    def _get_report_values(self, docids, data):
        month = data.get('month')
        year = data.get('year')
        month_display = data.get('month_display')
        month = int(month)
        year = int(year)

        days = monthrange(year, month)[1]
        start_date = date(year, month, 1)                         
        end_date = date(year, month, days)

        sales_orders = self.env['diet.subscription.order'].search([
            ('actual_start_date', '>=', start_date),
            ('state', '=', 'in_progress'),
            ('actual_start_date', '<=', end_date)
        ])

        plan_counts = {}
        plan_totals = {}

        for order in sales_orders:
            if order.plan_id:
                plan_name = order.plan_id.name
                grand_total = order.grand_total

                if plan_name not in plan_counts:
                    plan_counts[plan_name] = 0
                plan_counts[plan_name] += 1

                if plan_name not in plan_totals:
                    plan_totals[plan_name] = 0.0
                plan_totals[plan_name] += grand_total

        report_data = {
            
            'plan_data': []
        }

        for plan_name, count in plan_counts.items():
            report_data['plan_data'].append({
                'plan_name': plan_name,
                'plan_counts': count,
                'plan_revenue': plan_totals[plan_name]
            })

        return {
            'doc_ids': sales_orders,
            'data': data,
            'report_data': report_data,
            'month': month_display,
        }
