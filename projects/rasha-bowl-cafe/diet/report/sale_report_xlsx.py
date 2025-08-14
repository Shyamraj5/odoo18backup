from odoo import models
from datetime import datetime, timedelta , date
from calendar import monthrange


class SaleReport(models.AbstractModel):
    _name = "report.sale_report_xlsx"
    _description = "Report for Sale Report"
    _inherit = "report.report_xlsx.abstract"


    def generate_xlsx_report(self, workbook, data, lines):
        main_head = workbook.add_format({
            "font_size": 20,
            "bottom": True,
            "right": True,
            "left": True,
            "top": True,
            "align": "center",
            "bold": True,
            "valign": "vcenter",
            "bg_color": "#eb3489",
            "font_color": "#ffffff"
        })

        sub_head = workbook.add_format({
            "font_size": 11,
            "bottom": True,
            "right": True,
            "left": True,
            "top": True,
            "bold" : True,
            "valign": "vcenter",
            "align" : "center"
        })
        
        style_total = workbook.add_format({
            "bold": True,
            "align": "right"
        })

        style_value = workbook.add_format({
            "align": "right"
        })

        month = int(data['month'])
        year = int(data['year'])
        days = monthrange(year, month)[1]

        worksheet = workbook.add_worksheet("Sale Report")
        worksheet.merge_range(
            0,0,0,days+2, "SALE REPORT", main_head
        )
        worksheet.set_row(0, 40)
        worksheet.set_row(1, 30)
        worksheet.set_column("A:A", 3)
        worksheet.set_column("B:B",12)
        worksheet.set_column(days+2,days+2, 10)
        worksheet.write("A2", "NO", sub_head)
        worksheet.write("B2", "CUSTOMER", sub_head)
        for col in range(2, days + 2):  # Start from column C (index 2)
            day_col = col - 2 + 1
            worksheet.write(1, col, day_col, sub_head)
        worksheet.write(1, days+2, "Total", sub_head)

        calendar_entry_query = """
            SELECT
                DISTINCT(partner_id)
            FROM
                customer_meal_calendar
            WHERE
                start_date >= %s
                AND end_date <= %s
                AND state IN ('active', 'active_with_meal')
        """
        self.env.cr.execute(calendar_entry_query, (date(year, month, 1), date(year, month, days)))
        partner_ids = self.env.cr.fetchall()
        row=2
        sl_no = 1 
        day_total = {day: 0 for day in range(1, days + 1)} 
        day_total["total"] = 0
        for customer in partner_ids:
            col=1
            customer = self.env['res.partner'].browse(customer[0])
            worksheet.write(row, 0, sl_no)
            worksheet.write(row, col, customer.name) 
            customer_calendar_entries_query = """
                SELECT
                    DISTINCT(id)
                FROM
                    customer_meal_calendar
                WHERE
                    partner_id = %s
                    AND date >= %s
                    AND date <= %s
                    AND state IN ('active', 'active_with_meal')
            """
            self.env.cr.execute(customer_calendar_entries_query, (customer.id, date(year, month, 1), date(year, month, days)))
            calendar_entry_ids = self.env.cr.fetchall()
            formatted_calendar_entry_ids = [entry_id[0] for entry_id in calendar_entry_ids]
            user_total = 0
            for day in range(1, days+1):
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
                    column_amount = subscription_amount / subscription.package_days
                worksheet.write(row, col+1, f"{column_amount:.4f}",style_value)
                user_total += column_amount
                day_total[day] += column_amount
                col += 1
            worksheet.write(row, days + 2, f"{user_total:.4f}", style_total)
            day_total["total"] += user_total
            row += 1
            sl_no += 1
        
        row += 1
        worksheet.merge_range(
            row,0,row,1, "Total", sub_head
        )
        col=2
        for day in day_total:
            worksheet.write(row,col,f"{day_total[day]:.4f}", style_total)
            col+=1



