from odoo import models, fields



class CustomerKitchenReportWizard(models.TransientModel):
    _name = "customer.kitchen.report.wizard"
    _description = "Wizard for Customer Kitchen Report"


    date = fields.Date(string ="Date", required =True)
    plan_category_id =fields.Many2one('plan.category', string ="Plan Category")
    meal_category_id =fields.Many2one('meals.category', string ="Meal category")


        
    def print_excel(self):
        data = {
            "date" : self.date
        }
        return self.env.ref("diet.action_customer_daily_report").report_action(self, data =data, config =False)
    
    def  print_pdf(self):
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
        dict1 ={}
        for meals in meal_calendar:
            customer = meals.partner_id.customer_sequence_no
            id =meals.partner_id.name
            plan = meals.so_id.plan_id.name
            category = meals.meal_category_id.name
            meal = meals.meal_id.name

            if customer not in dict1:
                dict1[customer] ={"id" : id, "plan": plan, "meal_type":{category:meal}}
            if category not in dict1[customer]['meal_type']:
                dict1[customer]["meal_type"][category] = meal
        persons =meal_calendar.mapped('partner_id')
        total_person =len(persons)
        categories =meal_calendar.mapped('plan_category_id')
        plan_dict ={}
        for category in categories:
            partners = meal_calendar.filtered(lambda self: self.plan_category_id.id == category.id).mapped('partner_id')
            length = len(partners)
            if category.name not in plan_dict:
                plan_dict[category.name] = length
        meal_len = len(meal_calendar)
        meal_dict={}
        meal_categ = meal_calendar.mapped('meal_category_id')
        for meal_cat in meal_categ:
            meal_length = meal_calendar.filtered(lambda self: self.meal_category_id.id == meal_cat.id)
            length = len(meal_length)
            if meal_cat.name not in meal_dict:
                meal_dict[meal_cat.name] = length
            
        data = {
            "date" : self.date.strftime("%d-%m-%Y"),
            "calendar":dict1,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country,
            "persons":total_person,
            "plan_dict": plan_dict,
            "meal_dict": meal_dict,
            "total_meals":meal_len
        }
        return self.env.ref("diet.action_customer_daily_report_pdf").report_action(self, data =data, config =False)
    
    def preview_report(self):
        domain =[('date','=', self.date),('state','=','active')]
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
        dict1 ={}
        for meals in meal_calendar:
            customer = meals.partner_id.customer_sequence_no
            id =meals.partner_id.name
            plan = meals.plan_category_id.name
            category = meals.meal_category_id.name
            meal = meals.meal_id.name

            if customer not in dict1:
                dict1[customer] ={"id" : id, "plan": plan, "meal_type":{category:meal}}
            if category not in dict1[customer]['meal_type']:
                dict1[customer]["meal_type"][category] = meal
        persons =meal_calendar.mapped('partner_id')
        total_person =len(persons)
        categories =meal_calendar.mapped('plan_category_id')
        plan_dict ={}
        for category in categories:
            partners = meal_calendar.filtered(lambda self: self.plan_category_id.id == category.id).mapped('partner_id')
            length = len(partners)
            if category.name not in plan_dict:
                plan_dict[category.name] = length
        meal_len = len(meal_calendar)
        meal_dict={}
        meal_categ = meal_calendar.mapped('meal_category_id')
        for meal_cat in meal_categ:
            meal_length = meal_calendar.filtered(lambda self: self.meal_category_id.id == meal_cat.id)
            length = len(meal_length)
            if meal_cat.name not in meal_dict:
                meal_dict[meal_cat.name] = length
            
        data = {
            "date" : self.date.strftime("%d-%m-%Y"),
            "calendar":dict1,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country,
            "persons":total_person,
            "plan_dict": plan_dict,
            "meal_dict": meal_dict,
            "total_meals":meal_len
        }
        return self.env.ref("diet.action_customer_daily_report_pdf_preview").report_action(self, data =data, config =False)