from odoo import models
from datetime import datetime


class CustomerDailyReport(models.AbstractModel):
    _name = "report.customer_daily_report_xlsx"
    _description = "Report for customer daily meals"
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
                    "bg_color": "#b7dfa9"

            }
        )
        format1b =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "align": "center",
                "valign": "vcenter",
                "num_format": "#,##0.00",
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
                "font_size": 20,
                "bottom" : True,
                "right" : True,
                "left": True,
                "top": True,
                "align": "center",
                "bold": True,
                "bg_color" :"#8bc388",
                "font_color" : "white",
                "valign": "vcenter"
            }
        )
        format1e =workbook.add_format(
            {
                "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "right",
                    "bold": True,
                    "valign": "vcenter",
                })
        format1f =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "align": "left",
                "valign": "vcenter",
                "num_format": "#,##0.00",
                })
        format1g =workbook.add_format(
            {
                "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "right",
                    "valign": "vcenter",
                })
        format1h =workbook.add_format(
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
        date = lines.date.strftime("%d-%m-%Y")

        worksheet = workbook.add_worksheet("CUSTOMER DAILY REPORT")
        worksheet.merge_range("A1:F1", "FEED", format1d)
        worksheet.merge_range("A2:F2", "CUSTOMER DAILY REPORT                 " + "Date: " + date, format1h)
        worksheet.set_row(0, 50)
        worksheet.set_row(1, 30)
        worksheet.set_column("A:A", 7)
        worksheet.set_column("B:B", 15)
        worksheet.set_column("C:C", 30)
        worksheet.set_column("D:D", 20)
        worksheet.set_column("E:E", 20)
        worksheet.set_column("F:F", 30)
        worksheet.write("A3", "SI NO", format1a)
        worksheet.write("B3", "CUSTOMER ID",format1a)
        worksheet.write("C3", "CUSTOMER",format1a)
        worksheet.write("D3", "PLAN CATEGORY",format1a)
        worksheet.write("E3", "MEAL CATEGORY",format1a)
        worksheet.write("F3", "MEAL",format1a)

        domain =[('date','=', lines.date),('state','=','active')]
        if lines.plan_category_id.id:
            domain.append(('plan_category_id','=', lines.plan_category_id.id))
        if lines.meal_category_id.id:
            domain.append(('meal_category_id','=', lines.meal_category_id.id))
        meal_calendar = self.env['customer.meal.calendar'].search(domain)
        dict ={}
        for meals in meal_calendar:
            customer = meals.partner_id.customer_sequence_no
            id =meals.partner_id.name
            plan = meals.plan_category_id.name
            category = meals.meal_category_id.name
            meal = meals.meal_id.name

            if customer not in dict:
                dict[customer] ={"id" : id, "plan": plan, "meal_type":{category:meal}}
            if category not in dict[customer]['meal_type']:
                dict[customer]["meal_type"][category] = meal


        row = 4
        i = 0
        for name,values in dict.items():
            i += 1
            for meal_category, vals in values["meal_type"].items():
                worksheet.write("E%s" % row, meal_category, format1f)
                worksheet.write("F%s" % row, vals, format1f)
                row+=1
            total_row = row
            worksheet.write("E%s" %row,"Total", format1c)
            length =len(values["meal_type"])
            worksheet.write("F%s" %row,length, format1e)
            worksheet.merge_range("A%s:A%s" %(total_row - (length),total_row), str(int(i)), format1b)
            worksheet.merge_range("B%s:B%s" %(total_row - (length),total_row), name, format1b)
            worksheet.merge_range("C%s:C%s" %(total_row - (length),total_row), values["id"], format1b)
            worksheet.merge_range("D%s:D%s" %(total_row - (length),total_row), values["plan"], format1b)

            row+=2

        worksheet.write("C%s" %row,"TOTAL CUSTOMERS", format1c)
        worksheet.write("D%s" %row,len(dict), format1e)
        row+=1
        plan_category =meal_calendar.mapped('plan_category_id')
        for categ in plan_category:
            worksheet.write("C%s" %row,categ.name, format1g)
            partners =meal_calendar.filtered(lambda self: self.plan_category_id.id == categ.id).mapped('partner_id')
            worksheet.write("D%s" %row,len(partners), format1g)
            row+=1
        row+=1
        worksheet.write("C%s" %row,"TOTAL MEALS", format1c)
        worksheet.write("D%s" %row,len(meal_calendar), format1e)
        row+=1
        meal_categ = meal_calendar.mapped('meal_category_id')
        for meal_cat in meal_categ:
            worksheet.write("C%s" %row,meal_cat.name, format1g)
            meal_length = meal_calendar.filtered(lambda self: self.meal_category_id.id == meal_cat.id)
            worksheet.write("D%s" %row,len(meal_length), format1g)
            row+=1