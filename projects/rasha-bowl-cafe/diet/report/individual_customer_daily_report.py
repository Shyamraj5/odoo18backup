from odoo import models
from datetime import datetime


class IndividualCustomerDailyReport(models.AbstractModel):
    _name = "report.individual_customer_daily_report_xlsx"
    _description = "Report of Individual Customers about Daily Meals"
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
                    "bg_color": "#b7dfa9"
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
        format1i =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "align": "center",
                "valign": "vcenter",
                "bold": True,
                })
        
        date1 =lines.date.strftime("%d-%m-%Y")
        calendar_date=datetime.strptime(data['date'],"%Y-%m-%d")
        domain =['|',('state','=','active'),('state','=','active_with_meal')]
        if lines.date:
            domain.append(('date','=', lines.date))
        if lines.partner_id:
            domain.append(('partner_id','=',lines.partner_id.id))
        if lines.plan_category_id:
            domain.append(('plan_category_id','=',lines.plan_category_id.id))
        if lines.shift_id:
            domain.append(('partner_id.shift_id','=',lines.shift_id.id))
        meal_calendar = self.env['customer.meal.calendar'].search(domain)
        
        dict ={}
        
        for meals in meal_calendar:
            plan = meals.plan_category_id.name
            category = meals.meal_category_id.name
            meal = meals.meal_id.name
            recipe = meals.env['subscription.plan.meals'].search([('plan_id','=',meals.so_id.plan_id.id),('meal_id','=',meals.meal_id.id)])
            carbs =recipe.carbohydrates
            protein =recipe.protein
            fat =recipe.fats
            calorie =recipe.calorie
            
            

            dl = ''
            dislike_list =[]
            partner_dislike = meals.partner_id.dislikes_ids
            if partner_dislike:
                for x in partner_dislike:
                    y = meals.meal_id.ingredients_line_ids.mapped('ingredient_id')
                    for z in y:
                        if z.id == x.id:
                            dislike_list.append(x.name)
                dislike_list.sort()
                dl = ','.join(dislike_list)

            so_meal_lines = meals.so_id.mapped('meal_line_ids')
            portion=""
            for lines in so_meal_lines:
                if lines.meal_category_id.name == category:
                    portion =lines.portion_count

            customer = meals.partner_id.customer_sequence_no
            if customer not in dict:
                dict[customer]={"category":{category:{}},"id":meals.partner_id.name,
                                "shift":meals.partner_id.shift_id.shift,"notes":meals.partner_id.comments,
                                "snacks_count":0,"meals_count":0,
                                "plan":plan}
                categories_type = meal_calendar.search([('partner_id','=',meals.partner_id.id),('date','=',calendar_date),('state','=','active')])
                category_type=categories_type.mapped('meal_category_id')
                for type in category_type:
                    if type.is_snack == True:
                        dict[customer]['snacks_count'] += 1
                    else:
                        dict[customer]['meals_count'] += 1
            
            dict[customer]["category"][category]={"meal": meal,"dislike":dl,"portion":portion,"protein":protein,"carbs":carbs,"fat":fat,"calorie":calorie}
            
        for cus, cus_vals in dict.items():
            worksheet = workbook.add_worksheet(cus.upper() + " DESPATCH CARD")
            worksheet.merge_range("A1:H1", "FEED", format1d)
            worksheet.merge_range("A2:H2", "CUSTOMER DESPATCH CARD" +"                      "+ "Date: " + date1 +"                ", format1h)
            worksheet.merge_range("A3:H3",
                            "CUSTOMER NAME: "+ cus_vals['id'] + " "+  
                            "                                          "+"                                        CUSTOMER ID: "+ cus, 
                            format1a)
            if cus_vals['snacks_count'] > 0 and cus_vals['meals_count'] > 0:
                worksheet.merge_range("A4:H4","PLAN CATEGORY: " + cus_vals['plan'].upper() +" - "+ str(cus_vals['meals_count']) + " MEALS + "+str(cus_vals['snacks_count']) +" SNACKS",format1i)
            else:
                if cus_vals['meals_count'] > 0:
                    worksheet.merge_range("A4:H4","PLAN CATEGORY: " + cus_vals['plan'].upper() +" - "+ str(cus_vals['meals_count']) + " MEALS",format1i)
                if cus_vals['snacks_count'] > 0:
                    worksheet.merge_range("A4:H4","PLAN CATEGORY: " + cus_vals['plan'].upper() +" - "+ str(cus_vals['snacks_count']) +" SNACKS",format1i)

            if cus_vals['notes']:
                worksheet.merge_range("A5:H5","CUSTOMER NOTES: " + cus_vals['notes'],format1f)
            else:
                worksheet.merge_range("A5:H5","CUSTOMER NOTES: ",format1f)
            if cus_vals['shift']:
                worksheet.merge_range("A6:H6","DELIVERY TIME: "+ cus_vals['shift'],format1f)
            else:
                worksheet.merge_range("A6:H6","DELIVERY TIME: ",format1f)
            worksheet.set_row(0, 50)
            worksheet.set_row(1, 30)
            worksheet.set_row(2, 20)
            worksheet.set_row(3, 20)
            worksheet.set_row(4, 25)
            worksheet.set_row(5, 20)
            worksheet.set_column("A:A", 5)
            worksheet.set_column("B:B", 20)
            worksheet.set_column("C:C", 35)
            worksheet.set_column("D:D", 15)
            worksheet.set_column("E:E", 15)
            worksheet.set_column("F:F", 10)
            worksheet.set_column("G:G", 10)
            worksheet.set_column("H:H", 15)
            worksheet.write("A7", "SI NO", format1a)
            worksheet.write("B7", "MEAL CATEGORY",format1a)
            worksheet.write("C7", "MEAL",format1a)
            worksheet.write("D7", "PORTION",format1a)
            worksheet.write("E7", "PROTEIN",format1a)
            worksheet.write("F7", "CARBS",format1a)
            worksheet.write("G7", "FAT",format1a)
            worksheet.write("H7", "CALORIE",format1a)

            
            row =8
            i = 0
            for name,vals in cus_vals["category"].items():
                i += 1
                if vals["dislike"]:
                    worksheet.merge_range("A%s:A%s" % (row, row+1), str(int(i)),format1b)
                    worksheet.merge_range("B%s:B%s" % (row, row+1), name,format1b)
                    worksheet.merge_range("C%s:C%s" % (row, row+1), vals['meal'] + "\n" + "Avoid " + vals['dislike'],format1f)
                    worksheet.merge_range("D%s:D%s" % (row, row+1), vals['portion'],format1g)
                    worksheet.merge_range("E%s:E%s" % (row, row+1), round(vals['protein'],2),format1g)
                    worksheet.merge_range("F%s:F%s" % (row, row+1), round(vals['carbs'],2),format1g)
                    worksheet.merge_range("G%s:G%s" % (row, row+1), round(vals['fat'],2),format1g)
                    worksheet.merge_range("H%s:H%s" % (row, row+1), round(vals['calorie'],2),format1g)
                    row+=2
                else:
                    worksheet.write("A%s" % row, str(int(i)),format1b)
                    worksheet.write("B%s" % row, name,format1b)
                    worksheet.write("C%s" % row, vals['meal'],format1f)
                    worksheet.write("D%s" % row, vals['portion'],format1g)
                    worksheet.write("E%s" % row, round(vals['protein'],2),format1g)
                    worksheet.write("F%s" % row, round(vals['carbs'],2),format1g)
                    worksheet.write("G%s" % row, round(vals['fat'],2),format1g)
                    worksheet.write("H%s" % row, round(vals['calorie'],2),format1g)
                    row+=1
            row += 2
            worksheet.write("C%s" % row, "TOTAL MEALS",format1a)
            worksheet.write("D%s" % row,len(cus_vals["category"]) ,format1e)