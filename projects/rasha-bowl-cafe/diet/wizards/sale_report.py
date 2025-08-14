from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from datetime import timedelta, date, datetime
from calendar import monthrange
import calendar

MONTHS = [
    ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
]
YEARS = [(str(year), str(year)) for year in range(2020, 2030)]


class SaleReport(models.TransientModel):
    _name = "sale.report.wizard"
    _description = "Wizard for Sale Report"

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

    def print_excel(self):
        month_display = dict(self._fields['month'].selection).get(self.month)

        data = {
            "month": self.month,       # Pass the key
            "month_display": month_display,  # Pass the display name
            "year": self.year
        }
        return self.env.ref("diet.action_sale_report").report_action(self, data=data, config =False)
    
    # def preview(self):
    #     month = int(self.month)
    #     year = int(self.year)
    #     days = monthrange(year, month)[1]
    #     data = {
    #     'year': year,
    #     'month': calendar.month_name[month],
    #     'days': list(range(1, days + 1)),
    #     'customers': [],
    #     'day_totals': {day: 0 for day in range(1, days + 1)},
    #     'total': 0
    # }

    #     calendar_entries = self.env['customer.meal.calendar'].search([
    #         ('start_date', '>=', date(year, month, 1)),
    #         ('end_date', '<=', date(year, month, days)),
    #         ('state', 'in', ['active', 'active_with_meal'])
    #     ])
    #     customers = calendar_entries.mapped('partner_id')
    #     day_totals = {day: 0 for day in range(1, days + 1)}
    #     total = 0

    #     for sl_no, customer in enumerate(customers, start=1):
    #         customer_data = {
    #             'sl_no': sl_no,
    #             'name': customer.name,
    #             'daily_amounts': [],
    #             'total': 0
    #         }
    #         customer_calendar_entries = calendar_entries.filtered(lambda cal: cal.partner_id == customer)
    #         user_total = 0

    #         for day in range(1, days + 1):
    #             column_date = date(year, month, day)
    #             column_entries = customer_calendar_entries.filtered(lambda c_cal: c_cal.date == column_date)
    #             column_amount = 0
    #             if column_entries:
    #                 subscription = column_entries[0].so_id
    #                 subscription_amount = subscription.grand_total
    #                 column_amount = subscription_amount / subscription.package_days
    #             customer_data['daily_amounts'].append(column_amount)
    #             user_total += column_amount
    #             day_totals[day] += column_amount
            
    #         customer_data['total'] = user_total
    #         total += user_total
    #         data['customers'].append(customer_data)
        
    #     data['day_totals'] = [day_totals[day] for day in range(1, days + 1)]
    #     data['total'] = total

    #     return self.env.ref("diet.action_sale_report_preview").report_action(self, data=data, config=False)

    def prepare_values_for_component(self, month=False, year=False):
        month = int(month) if month else int(self.month)
        year = int(year) if year else int(self.year)
        days = monthrange(year, month)[1]
        data = {
            'year': year,
            'customers': [],
            'day_totals': [],
            'total': 0
        }

        calendar_entry_query = """
            SELECT
                DISTINCT(cmc.partner_id)
            FROM
                customer_meal_calendar cmc
            INNER JOIN
                diet_subscription_order csol ON
                csol.id = cmc.so_id
            WHERE
                cmc.start_date >= %s
                AND cmc.end_date <= %s
                AND cmc.state IN ('active', 'active_with_meal')
                AND csol.payment_status = 'paid'
                AND cmc.partner_id IS NOT NULL
                AND csol.grand_total > 0
        """
        self.env.cr.execute(calendar_entry_query, (date(year, month, 1), date(year, month, days)))
        partner_ids = self.env.cr.fetchall()
        day_totals = {day: 0 for day in range(1, days + 1)}
        total = 0
        sl_no = 1
        line = 1
        for partner_id in partner_ids:
            customer = self.env['res.partner'].browse(partner_id[0])
            customer_data = {
                'sl_no': sl_no,
                'name': customer.full_name,
                'customer_id': customer.customer_sequence_no,
                'daily_amounts': [],
                'total': 0
            }
            customer_calendar_entries_query = """
                SELECT
                    DISTINCT(cmc.id)
                FROM
                    customer_meal_calendar cmc
                INNER JOIN
                    diet_subscription_order csol ON
                    csol.id = cmc.so_id
                WHERE
                    cmc.partner_id = %s
                    AND cmc.date >= %s
                    AND cmc.date <= %s
                    AND cmc.state IN ('active', 'active_with_meal')
                    AND csol.payment_status = 'paid'
                    AND csol.grand_total > 0
            """
            self.env.cr.execute(customer_calendar_entries_query, (customer.id, date(year, month, 1), date(year, month, days)))
            calendar_entry_ids = self.env.cr.fetchall()
            formatted_calendar_entry_ids = [entry_id[0] for entry_id in calendar_entry_ids]
            user_total = 0
            for day in range(1, days + 1):
                column_date = date(year, month, day)
                column_date = column_date.strftime('%Y-%m-%d')
                column_entries_query = """
                    SELECT
                        DISTINCT(so_id)
                    FROM
                        customer_meal_calendar
                    WHERE
                        date = %s
                        AND id IN %s
                """
                self.env.cr.execute(column_entries_query, (column_date, tuple(formatted_calendar_entry_ids)))
                column_entries = self.env.cr.fetchall()
                column_amount = 0
                if column_entries:
                    subscription = self.env['diet.subscription.order'].browse(column_entries[0])
                    subscription_amount = subscription.grand_total
                    subscription_days = len(set(subscription.meal_calendar_ids.filtered(lambda x: x.state in ['active', 'active_with_meal']).mapped('date')))
                    column_amount = subscription_amount / subscription_days
                vals = {
                    'line': line,
                    'amount': column_amount
                }
                customer_data['daily_amounts'].append(vals)
                user_total += column_amount
                day_totals[day] += column_amount
                line += 1
            line += 1
            sl_no += 1
            customer_data['total'] = user_total
            total += user_total
            data['customers'].append(customer_data)
        for day in range(1, days + 1):
            vls = {
                'day': day,
                'amount': day_totals[day]
            }
            data['day_totals'].append(vls)
        data['total'] = total

        return data
