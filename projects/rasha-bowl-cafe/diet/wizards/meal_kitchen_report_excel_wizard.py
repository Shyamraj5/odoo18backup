from odoo import models, fields
from datetime import date



class KitchenReportWizard(models.TransientModel):
    _name = "meal.kitchen.report.wizard"
    _description = "Wizard for Kitchen Report of Meals"


    date = fields.Date(string ="Date", required =True, default = date.today())
    plan_category_id =fields.Many2one('plan.category', string ="Plan category")
    meal_category_id =fields.Many2one('meals.category', string ="Meal category")

    
    def print_excel(self):
        data = {
            "date" : self.date
        }
        return self.env.ref("diet.action_meal_kitchen_report").report_action(self, data =data, config =False)
    
    def print_pdf(self):
        domain =[('date','=', self.date),('state','=','active_with_meal')]
        if self.plan_category_id.id:
            domain.append(('plan_category_id','=', self.plan_category_id.id))
        if self.meal_category_id.id:
            domain.append(('meal_category_id','=', self.meal_category_id.id))
        meal_calendar = self.env['customer.meal.calendar'].search(domain)
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip =company_id.zip
        country =company_id.country_id.name

            
        dict={}
        for meal in meal_calendar:
            plan_categ = meal.so_id.plan_id.plan_category_id.name
            recipe = meal.meal_id.default_code
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
        persons =meal_calendar.mapped('partner_id')
        total_person =len(persons)
        categories =meal_calendar.mapped('plan_category_id')
        plan_dict ={}
        for category in categories:
            partners = meal_calendar.filtered(lambda self: self.plan_category_id.id == category.id).mapped('partner_id')
            length = len(partners)
            if category.name not in plan_dict:
                plan_dict[category.name] = length
        category_dict ={}
        meal_categories =meal_calendar.mapped('meal_category_id')
        for meal_c in meal_categories:
            if meal_c not in category_dict:
                meal_cat_count = len(meal_calendar.filtered(lambda self: self.meal_category_id.id == meal_c.id))
                meal_cat =meal_c.name
                category_dict[meal_cat]= meal_cat_count
        meals_count =len(meal_calendar)
        data = {
            "date" : self.date.strftime("%d-%m-%Y"),
            "calendar" :dict,
            "persons" : total_person,
            "plan_summary": plan_dict,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country,
            "meals_count":meals_count,
            "meal_summary" :category_dict

        }
        return self.env.ref("diet.action_daily_meals_report_pdf").report_action(self, data =data, config =False)
    
    def preview_report(self):
        domain =[('date','=', self.date)]
        if self.plan_category_id.id:
            domain.append(('plan_category_id','=', self.plan_category_id.id))
        if self.meal_category_id.id:
            domain.append(('meal_category_id','=', self.meal_category_id.id))
        meal_calendar = self.env['customer.meal.calendar'].search(domain)
        company_id =self.env.company
        company =company_id.name
        street =company_id.street
        street2 =company_id.street2
        city =company_id.city
        state =company_id.state_id.name
        zip =company_id.zip
        country =company_id.country_id.name
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
        persons =meal_calendar.mapped('partner_id')
        total_person =len(persons)
        categories =meal_calendar.mapped('plan_category_id')
        plan_dict ={}
        for category in categories:
            partners = meal_calendar.filtered(lambda self: self.plan_category_id.id == category.id).mapped('partner_id')
            length = len(partners)
            if category.name not in plan_dict:
                plan_dict[category.name] = length
        category_dict ={}
        meal_categories =meal_calendar.mapped('meal_category_id')
        for meal_c in meal_categories:
            if meal_c not in category_dict:
                meal_cat_count = len(meal_calendar.filtered(lambda self: self.meal_category_id.id == meal_c.id))
                meal_cat =meal_c.name
                category_dict[meal_cat]= meal_cat_count
        meals_count =len(meal_calendar)
        data = {
            "date" : self.date.strftime("%d-%m-%Y"),
            "calendar" :dict,
            "persons" : total_person,
            "plan_summary": plan_dict,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country,
            "meals_count":meals_count,
            "meal_summary" :category_dict

        }
       
        return self.env.ref("diet.action_daily_meals_report_pdf_preview").report_action(self, data =data, config =False)