from odoo import models, fields



class IndividualCustomerDailyReportWizard(models.TransientModel):
    _name = "individual.customer.daily.report.wizard"
    _description = "Wizard for Individual Customer Daily Report"


    date = fields.Date(string ="Date", required =True)
    partner_id =fields.Many2one('res.partner', string ="Customer")
    shift_id = fields.Many2one('customer.shift', string='Delivery Time')
    plan_category_id = fields.Many2one('plan.category', string='Plan Category')

        
    def print_excel(self):
        data = {
            "date" : self.date
        }
        return self.env.ref("diet.action_individual_customer_daily_report").report_action(self, data =data, config =False)
    
    def print_pdf(self):
        domain=['|',('state','=','active'),('state','=','active_with_meal')]
        if self.date:
            domain.append(('date','=', self.date))
        if self.partner_id:
            domain.append(('partner_id','=',self.partner_id.id))
        if self.plan_category_id:
            domain.append(('plan_category_id','=',self.plan_category_id.id))
        if self.shift_id:
            domain.append(('partner_id.shift_id','=',self.shift_id.id))
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
        plan = False
        protein = 0
        carbs = 0
        fat = 0
        calorie = 0
        for meals in meal_calendar:
            plan = meals.plan_category_id.name
            category = meals.meal_category_id.name
            meal = meals.meal_id.name
            recipe = meals.env['subscription.plan.meals'].search([('plan_id','=',meals.so_id.plan_id.id),('meal_id','=',meals.meal_id.id)])
            carbs =recipe.carbohydrates
            protein =recipe.protein
            fat =recipe.fats
            calorie =recipe.calorie
            category_type = meal_calendar.mapped('meal_category_id')
            type_meal= 0
            type_snack= 0
            for type in category_type:
                if type.is_snack == True:
                    type_snack += 1
                else:
                    type_meal += 1
           
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
            if customer not in dict1:
                dict1[customer]={"category":{category:{}},"id":meals.partner_id.name,
                                 "shift":meals.partner_id.shift_id.shift,"notes":meals.partner_id.comments,
                                 "snacks_count":0,"meals_count":0,
                                "plan":plan}
                categories_type = meal_calendar.search([('partner_id','=',meals.partner_id.id),('date','=',self.date),('state','=','active')])
                category_types=categories_type.mapped('meal_category_id')
                for type in category_types:
                    if type.is_snack == True:
                        dict1[customer]['snacks_count'] += 1
                    else:
                        dict1[customer]['meals_count'] += 1
            dict1[customer]["category"][category]={"meal": meal,"dislike":dl,"portion":portion,"protein":protein,"carbs":carbs,"fat":fat,"calorie":calorie}
        
        total_meals =len(dict1)
        
        data = {
            "date" : self.date.strftime('%d-%m-%Y'),
            "name" : self.partner_id.name,
            "calendar" : dict1,
            "plan": plan,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country,
            "total_meals":total_meals
        }
        return self.env.ref("diet.action_individual_customer_daily_report_pdf").report_action(self, data =data, config =False)
    

    def preview_report(self):
        domain=['|',('state','=','active'),('state','=','active_with_meal')]
        if self.date:
            domain.append(('date','=', self.date))
        if self.partner_id:
            domain.append(('partner_id','=',self.partner_id.id))
        if self.plan_category_id:
            domain.append(('plan_category_id','=',self.plan_category_id.id))
        if self.shift_id:
            domain.append(('partner_id.shift_id','=',self.shift_id.id))
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
        type_meal= 0
        type_snack= 0
        plan = False
       
        protein = 0
        carbs = 0
        fat = 0
        calorie = 0
        for meals in meal_calendar:
            plan = meals.plan_category_id.name
            category = meals.meal_category_id.name
            meal = meals.meal_id.name
            recipe = meals.env['subscription.plan.meals'].search([('plan_id','=',meals.so_id.plan_id.id),('meal_id','=',meals.meal_id.id)])
            carbs =recipe.carbohydrates
            protein =recipe.protein
            fat =recipe.fats
            calorie =recipe.calorie
            category_type = meal_calendar.mapped('meal_category_id')
            type_meal= 0
            type_snack= 0
            customer = meals.partner_id.customer_sequence_no
            for type in category_type:
                if type.is_snack == True:
                    type_snack += 1
                else:
                    type_meal += 1
         
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
            if customer not in dict1:
                dict1[customer]={"category":{category:{}},"id":meals.partner_id.name,
                                 "shift":meals.partner_id.shift_id.shift,"notes":meals.partner_id.comments,
                                 "snacks_count":0,"meals_count":0,
                                "plan":plan}
                categories_type = meal_calendar.search([('partner_id','=',meals.partner_id.id),('date','=',self.date),('state','=','active')])
                category_types=categories_type.mapped('meal_category_id')
                for type in category_types:
                    if type.is_snack == True:
                        dict1[customer]['snacks_count'] += 1
                    else:
                        dict1[customer]['meals_count'] += 1
            dict1[customer]["category"][category]={"meal": meal,"dislike":dl,"portion":portion,"protein":protein,"carbs":carbs,"fat":fat,"calorie":calorie}
        total_meals =len(dict1)
        data = {
            "date" : self.date.strftime('%d-%m-%Y'),
            "name" : self.partner_id.name,
            "calendar" : dict1,
            "snack_type":type_snack,
            "meal_type": type_meal,
            "plan": plan,
            "company":company,
            "street":street,
            "street2":street2,
            "city": city,
            "state":state,
            "zip_code":self.env.company.zip,
            "country":country,
            "total_meals":total_meals
        }
        return self.env.ref("diet.action_individual_customer_daily_report_pdf_preview").report_action(self, data =data, config =False)