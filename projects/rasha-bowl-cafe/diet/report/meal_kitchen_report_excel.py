from odoo import models
from datetime import datetime, timedelta


class MealKitchenReport(models.AbstractModel):
    _name = "report.meal_kitchen_report_xlsx"
    _description = "Report for Kitchen with meals"
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
                "valign": "vcenter",
                "num_format": "#,##0.00",
                })
        format1f =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "right",
                    "bold": True,
                    "valign": "vcenter",

            }
        )
        format1g =workbook.add_format(
            {
                "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "left",
                    "bold": True,
                    "valign": "vcenter",
                    "font_color" : "#8bc388",
                })
        format1h =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "right",
                    "bold": True,
                    "valign": "vcenter",
                    "bg_color": "#8bc388"

            }
        )
        date = lines.date.strftime("%d-%m-%Y")
        worksheet = workbook.add_worksheet("DAILY MEALS REPORT")
        worksheet.merge_range("A1:H1", "FEED", format1d)
        if lines.meal_category_id:
            worksheet.merge_range("A2:H2", "DAILY MEALS REPORT ("+lines.meal_category_id.name.upper()+")              " + "                 Date :"+ data['date'], format1a)
        else:
            worksheet.merge_range("A2:H2", "DAILY MEALS REPORT              " + "                 Date :"+ date, format1a)
        worksheet.set_row(0, 50)
        worksheet.set_row(1, 30)
        worksheet.set_row(2, 20)
        worksheet.set_column("A:A", 5)
        worksheet.set_column("B:B", 15)
        worksheet.set_column("C:C", 25)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 5)
        worksheet.set_column("F:F", 5)
        worksheet.set_column("G:G", 5)
        worksheet.set_column("H:H", 20)
        domain =[('date','=', lines.date),'|',('state','=','active'),('state','=','active_with_meal')]
        if lines.plan_category_id.id:
            domain.append(('plan_category_id','=', lines.plan_category_id.id))
        if lines.meal_category_id.id:
            domain.append(('meal_category_id','=', lines.meal_category_id.id))
        meal_calendar = self.env['customer.meal.calendar'].search(domain)

        dict={}
        for meal in meal_calendar:
            plan_categ = meal.plan_category_id.name
            recipe = meal.env['subscription.plan.meals'].search([('plan_id','=',meal.so_id.plan_id.id),('meal_id','=',meal.meal_id.id)]).name
            item = meal.meal_id.name
            meal_categ = meal.meal_category_id
            meal_category = meal_categ.name

            dl = ''
            dislike_list =[]
            partner_dislike = meal.partner_id.dislikes_ids
            if partner_dislike:
                for x in partner_dislike:
                    y = meal.meal_id.ingredients_line_ids.mapped('ingredient_id')
                    for z in y:
                        if z.id == x.id:
                            dislike_list.append(x.name)
                dislike_list.sort()
                dl = ','.join(dislike_list)

            if plan_categ not in dict:
                dict[plan_categ] = {}
            if meal_category not in dict[plan_categ]:
                dict[plan_categ][meal_category]={}
            if recipe not in dict[plan_categ][meal_category]:
                dict[plan_categ][meal_category][recipe]={}
            if item not in dict[plan_categ][meal_category][recipe]:
                dict[plan_categ][meal_category][recipe][item]={"qty" : 0,"1": 0,"1.5":0,"2":0,"dislike":{dl:{"count":0,"1": 0,"1.5":0,"2":0}}}
            if dl not in dict[plan_categ][meal_category][recipe][item]["dislike"]:
                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]= {"count":1,"1": 0,"1.5":0,"2":0}
            else:
                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]["count"] += 1

            dict[plan_categ][meal_category][recipe][item]["qty"]+=1

            so_meal_lines = meal.so_id.mapped('meal_line_ids')
            for lines in so_meal_lines:
                if lines.meal_category_id.id == meal_categ.id:
                    if lines.portion_count == 1:
                        dict[plan_categ][meal_category][recipe][item]["1"] += 1
                        if dl:
                            if dl in dict[plan_categ][meal_category][recipe][item]["dislike"]:
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]["1"] += 1
                            else:
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl] = {"count": 0, "1": 0, "1.5": 0, "2": 0}
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]["1"] += 1
                    if lines.portion_count == 1.5:
                        dict[plan_categ][meal_category][recipe][item]["1.5"] += 1
                        if dl:
                            if dl in dict[plan_categ][meal_category][recipe][item]["dislike"]:
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]["1.5"] += 1
                            else:
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl] = {"count": 0, "1": 0, "1.5": 0, "2": 0}
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]["1.5"] += 1
                    if lines.portion_count == 2:
                        dict[plan_categ][meal_category][recipe][item]["2"] += 1
                        if dl:
                            if dl in dict[plan_categ][meal_category][recipe][item]["dislike"]:
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]["2"] += 1
                            else:
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl] = {"count": 0, "1": 0, "1.5": 0, "2": 0}
                                dict[plan_categ][meal_category][recipe][item]["dislike"][dl]["2"] += 1
        
        row = 3
        
        for name, values in dict.items():
            plan_merge_range='A{}:H{}'.format(row,row)
            worksheet.merge_range(plan_merge_range, name.upper(), format1c)
            row += 1
            worksheet.write("A%s" %row, "NO", format1a)
            worksheet.write("B%s" %row, "RECIPE CODE",format1a)
            worksheet.write("C%s" %row, "MEAL",format1a)
            worksheet.write("D%s" %row, "PERSONS",format1a)
            worksheet.write("E%s" %row, "1",format1a)
            worksheet.write("F%s" %row, "1.5",format1a)
            worksheet.write("G%s" %row, "2",format1a)
            worksheet.write("H%s" %row, "TOTAL PORTIONS",format1a)
            row += 1
            i = 0
            sum_meals =[]
            sum_portion1 =[]
            sum_portion_one_half =[]
            sum_portion_double =[]
            sum_total_portion =[]
            for category, vals in values.items():
                plan_merge_range='A{}:H{}'.format(row,row)
                worksheet.merge_range(plan_merge_range, category.upper(), format1c)
                row += 1
                
                
                for recipes, val in vals.items():
                    i += 1
                    for items, pair in val.items():
                        sum_meals.append(pair["qty"])
                        sum_portion1.append(pair["1"])
                        sum_portion_one_half.append(pair["1.5"])
                        sum_portion_double.append(pair["2"])
                        l = 0
                        for dislike, vall in pair["dislike"].items():
                            if dislike:
                                l += 1
                            
                        
                        worksheet.merge_range("A%s:A%s" %(row,row+l), str(int(i)), format1b)
                        worksheet.merge_range("B%s:B%s" % (row,row+l), recipes, format1b)
                        if l ==0:
                            worksheet.write("A%s" %row, str(int(i)), format1b)
                            worksheet.write("B%s" % row, recipes, format1b)
                        worksheet.write("C%s" % row, items, format1b)
                        worksheet.write("D%s" % row, pair["qty"], format1f)
                        worksheet.write("E%s" % row, pair["1"], format1f)
                        worksheet.write("F%s" % row, pair["1.5"], format1f)
                        worksheet.write("G%s" % row, pair["2"], format1f)
                        total_portion = pair["1"] + (1.5 * pair["1.5"])+ (2*pair["2"])
                        sum_total_portion.append(total_portion)
                        worksheet.write("H%s" % row, total_portion, format1f)
                        row +=1
                        for dislik, portion in pair["dislike"].items():
                            if dislik:
                                worksheet.write("C%s" % row, "Avoid " + dislik , format1e)
                                worksheet.write("D%s" % row, portion['count'], format1b)
                                worksheet.write("E%s" % row, portion["1"], format1b)
                                worksheet.write("F%s" % row, portion["1.5"], format1b)
                                worksheet.write("G%s" % row, portion["2"], format1b)
                                total= portion["1"] + (1.5 * portion["1.5"])+ (2*portion["2"])
                                worksheet.write("H%s" % row, total, format1b)
                                row+=1
                           
                        
                            
            #...........................Total meals in a plan category...............................
            worksheet.merge_range("A%s:C%s" % (row,row), " Total" , format1f)
            worksheet.write("D%s" % row, sum(sum_meals) , format1f)
            worksheet.write("E%s" % row, sum(sum_portion1) , format1f)
            worksheet.write("F%s" % row, sum(sum_portion_one_half) , format1f)
            worksheet.write("G%s" % row, sum(sum_portion_double) , format1f)
            worksheet.write("H%s" % row, sum(sum_total_portion) , format1f)
            row+=2
            
        row += 2
        worksheet.write("C%s" %row, "Total Persons", format1a)
        persons =meal_calendar.mapped('partner_id')
        worksheet.write("D%s" %row, len(persons), format1h)
        row +=1
        categories =meal_calendar.mapped('plan_category_id')
        
        for category in categories:
            worksheet.write("C%s" %row, category.name, format1e) 
            partners = meal_calendar.filtered(lambda self: self.plan_category_id.id == category.id).mapped('partner_id')
            worksheet.write("D%s" %row,len(partners), format1b)
            row+=1

        worksheet.write("C%s" %row, "Total Meals", format1a)
        worksheet.write("D%s" %row, len(meal_calendar), format1h)
        row +=1
        category_dict ={}
        meal_categories =meal_calendar.mapped('meal_category_id')
        for meal_c in meal_categories:
            if meal_c not in category_dict:
                meal_cat_count = len(meal_calendar.filtered(lambda self: self.meal_category_id.id == meal_c.id))
                meal_cat =meal_c.name
                category_dict[meal_cat]= meal_cat_count
        for c ,v in category_dict.items():
            worksheet.write("C%s" %row, c, format1e)
            worksheet.write("D%s" %row, v, format1b)
            row +=1
            
        
