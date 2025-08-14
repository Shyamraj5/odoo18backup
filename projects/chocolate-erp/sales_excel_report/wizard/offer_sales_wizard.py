from odoo import models, fields
from datetime import datetime
import calendar

MONTHS = [
    ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
]
YEARS = [(str(year), str(year)) for year in range(2020, 2050)]


class OfferSalesWizard(models.TransientModel):
    _name = 'offer.sales.wizard'
    _description = 'Offer Sales Wizard'

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
        month = int(self.month)
        year = int(self.year)

        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1])

        sale_orders = self.env['sale.order'].search([
            ('date_order', '>=', start_date),
            ('date_order', '<=', end_date),
            ('state', 'in', ['sale', 'done']),
            ('order_line.offer_id', '!=', False)
        ])

        sales_data = []

        def process_order(order):
            data = []
            for line in order.order_line:
                data.append({
                    'date': order.date_order.strftime('%Y-%m-%d') if order.date_order else '',
                    'product': line.product_id.display_name or '',
                    'salesman': order.user_id.name or '',
                    'total_sales_amount': line.price_total,
                    'total_profit': line.margin if hasattr(line, 'margin') else 0.0,
                    'units_sold': line.product_uom_qty,
                })
            return data

        for order in sale_orders:
            sales_data.extend(process_order(order))

        sales_data.sort(key=lambda x: x['date'])

        return self.env.ref('sales_excel_report.action_offer_sales_report').report_action(
            self, data={'sales_data': sales_data, 'month': dict(MONTHS)[self.month], 'year': self.year}
        )