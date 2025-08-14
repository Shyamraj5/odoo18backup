from odoo import models
from datetime import datetime, timedelta


class MealCalendarReport(models.AbstractModel):
    _name = "report.meal_calendar_report_xlsx"
    _description = "Report for Meal Calendar"
    _inherit = "report.report_xlsx.abstract"


    def generate_xlsx_report(self, workbook, data, lines):
        format1a =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "bold": True,
                    "valign": "vcenter",
                    "bg_color": "#8bc388"

            }
        )
        format1b =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "num_format": "#,##0.00",
                "text_wrap": True 
                })
        format1c =workbook.add_format(
            {
                "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "left",
                    "bold": True,
                    "valign": "vcenter",
                })
        format1d =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "valign": "vcenter",
            }
        )
        off_day =workbook.add_format(
            {
            "font_size": 11,
            "bottom": True,
            "right": True,
            "left": True,
            "top": True,
            "align": "center",
            "valign": "vcenter",
            "font_color": "red",
            "bold": True,
            }
        )
        start_date = datetime.strptime(data['date_from'],"%Y-%m-%d")
        end_date = datetime.strptime(data['date_to'],"%Y-%m-%d")

        worksheet = workbook.add_worksheet("MEAL CALENDAR REPORT")
        days = (end_date - start_date).days + 1
        merge_range = 'A1:{}'.format((chr(ord('E')+ days)+'1').upper())
        worksheet.merge_range(
            merge_range, "MEAL CALENDAR REPORT", format1a
        )
        date_merge_range ='A2:{}'.format((chr(ord('E')+ days)+'2').upper())
        worksheet.merge_range(
            date_merge_range, "Date: " + start_date.strftime("%d-%m-%Y") + " - " + end_date.strftime("%d-%m-%Y"), format1c
        )
        worksheet.set_row(0, 50)
        worksheet.set_row(1, 20)
        worksheet.set_column("A:A", 6)
        worksheet.set_column("B:B",14)
        worksheet.set_column("C:C", 30)
        worksheet.set_column("D:D", 30)
        worksheet.set_column("E:E", 15)
        worksheet.set_column("F:F", 50)
        worksheet.write("A3", "SL NO", format1a)
        worksheet.write("B3", "CUSTOMER ID",format1a)
        worksheet.write("C3", "CUSTOMER",format1a)
        worksheet.write("D3", "PLAN",format1a)
        worksheet.write("E3", "MEAL TYPE",format1a)


        calendar = self.env['customer.meal.calendar'].search([('date','>=', start_date),('date','<=', end_date),'|',('state','=','active'),('state','=','active_with_meal')])
        customer ={}

        date_column = 5
        for i in range(days):
            date = start_date + timedelta(days=i)
            worksheet.write(2, date_column, date.strftime("%d-%m-%Y"), format1a)
            worksheet.set_column(date_column, date_column,25)
            date_column += 1

        for records in calendar:
            id = records.partner_id.customer_sequence_no
            partner_name= records.partner_id.name
            plan = ', '.join(plan.name for plan in calendar.mapped('so_id.plan_id'))
            meal_type = records.meal_category_id.name
            date = str(records.date)
            meal = records.meal_id.name
            if id not in customer:
                customer[id] = {"meal_type":{}, "plan":plan, "cus_name":partner_name}
            if meal_type not in customer[id]["meal_type"]:
                customer[id]["meal_type"][meal_type] = []

            customer[id]["meal_type"][meal_type].append({'date': date, 'meal': meal})
        row = 4
        i = 0
        for cus_id, values in customer.items():
            i +=1
            sl_range ="A%s:A%s"%(row,(row + len(values["meal_type"])-1))
            worksheet.merge_range(sl_range, str(int(i)), format1d)
            cus_id_range ="B%s:B%s"%(row,(row + len(values["meal_type"])-1))
            worksheet.merge_range(cus_id_range, cus_id, format1d)
            customer_range ="C%s:C%s"%(row,(row + len(values["meal_type"])-1))
            worksheet.merge_range(customer_range, values["cus_name"], format1d)
            plan_range ="D%s:D%s"%(row,(row + len(values["meal_type"])-1))
            worksheet.merge_range(plan_range, values["plan"], format1d)
            for type, vals in values["meal_type"].items():
                worksheet.write("E%s" % row, type, format1b)
                day = (end_date - start_date).days + 1
                meal_column = 5
                for d in range(day):
                    date = start_date + timedelta(days=d)
                    ml = []
                    for meals in vals:
                        if meals['date'] == str(date.date()):
                            ml.append(meals['meal'])
                    if ml:
                        worksheet.write(row-1, meal_column, ','.join(ml), format1b)
                    else:
                        worksheet.write(row-1, meal_column, 'Off Day', off_day)
                    meal_column += 1
                row +=1
            