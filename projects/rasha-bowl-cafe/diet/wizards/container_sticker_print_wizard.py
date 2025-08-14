from odoo import models, fields


class ContainerStickerPrintWizard(models.TransientModel):
    _name = "container.sticker.wizard"
    _description = "Wizard for Container Sticker Print"


    date = fields.Date(string ="Date", required =True)
    plan_id = fields.Many2one('subscription.package.plan', string =" Plan")
    meal_category_id= fields.Many2one('meals.category', string="Meal Category")


    def print_sticker(self):
        domain =[('date', '=', self.date),'|',('state','=','active'),('state','=','active_with_meal')]
        if self.plan_id:
            domain.append(('so_id.plan_id','=',self.plan_id.id))
        if self.meal_category_id:
            domain.append(('meal_category_id','=',self.meal_category_id.id))
        meal_calendar =self.env['customer.meal.calendar'].search(domain)
        sticker_list =[]
        sticker_dict ={}
        for calendar in meal_calendar:
            item = calendar.meal_id.name
            meal_categ = calendar.meal_category_id
            meal_category = meal_categ.name
            plan =calendar.so_id.plan_id.name
            partner_dislike = calendar.partner_id.dislikes_ids
            if plan not in sticker_dict:
                sticker_dict[plan] ={}
            if meal_category not in sticker_dict[plan]:
                sticker_dict[plan][meal_category] =[]
            
            
            dl = ''
            dislike_list =[]
            if partner_dislike:
                for x in partner_dislike:
                    y = calendar.meal_id.ingredients_line_ids.mapped('ingredient_id')
                    for z in y:
                        if z.id == x.id:
                            dislike_list.append(x.name)
                dislike_list.sort()
                dl = ','.join(dislike_list)
                sticker_dict[plan][meal_category].append({"meal" : item , "dislike":dl})
            else:
                sticker_dict[plan][meal_category].append({"meal" : item , "dislike":dl})
            sticker_list.append(sticker_dict)
        data ={
            "sticker_dict": sticker_dict,
            "date": self.date
        }
        return self.env.ref("diet.action_container_sticker_print").report_action(self, data =data, config =False)
    
    def print_sticker_preview(self):
        domain =[('date', '=', self.date),'|',('state','=','active'),('state','=','active_with_meal')]
        if self.plan_id:
            domain.append(('so_id.plan_id','=',self.plan_id.id))
        if self.meal_category_id:
            domain.append(('meal_category_id','=',self.meal_category_id.id))
        meal_calendar =self.env['customer.meal.calendar'].search(domain)
        sticker_list =[]
        sticker_dict ={}
        for calendar in meal_calendar:
            item = calendar.meal_id.name
            meal_categ = calendar.meal_category_id
            meal_category = meal_categ.name
            plan =calendar.so_id.plan_id.name
            partner_dislike = calendar.partner_id.dislikes_ids
            if plan not in sticker_dict:
                sticker_dict[plan] ={}
            if meal_category not in sticker_dict[plan]:
                sticker_dict[plan][meal_category] =[]
            
            
            dl = ''
            dislike_list =[]
            if partner_dislike:
                for x in partner_dislike:
                    y = calendar.meal_id.ingredients_line_ids.mapped('ingredient_id')
                    for z in y:
                        if z.id == x.id:
                            dislike_list.append(x.name)
                dislike_list.sort()
                dl = ','.join(dislike_list)
                sticker_dict[plan][meal_category].append({"meal" : item , "dislike":dl})
            else:
                sticker_dict[plan][meal_category].append({"meal" : item , "dislike":dl})
            sticker_list.append(sticker_dict)
        data ={
            "sticker_dict": sticker_dict,
            "date": self.date
        }
        return self.env.ref("diet.action_container_sticker_print_preview").report_action(self, data =data, config =False)