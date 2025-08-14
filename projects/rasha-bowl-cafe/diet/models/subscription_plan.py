# -*- coding: utf-8 -*-


from odoo import api, models, fields, _
from odoo.exceptions import ValidationError,UserError


class SubscriptionPlan(models.Model):
    _name = 'subscription.package.plan'
    _description = 'Subscription Package Plan'
    _inherit = ['mail.thread','mail.activity.mixin']

    sequence = fields.Integer('Sequence', copy=False)
    name = fields.Char(string='Plan Name', required=True)
    image = fields.Image(string ="Image")
    description = fields.Text(string ="Description")
    protein = fields.Float(string ="Protein", default=0.0)
    carbohydrates = fields.Float(string ="Carbs", default=0.0)
    fat = fields.Float(string ="Fat", default=0.0)
    calories = fields.Float(string ="Calories", store=True)
    start_date = fields.Date(string ="Start Date")
    duration_days = fields.Integer(string="Duration(Days)")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 store=True, domain="[('type', '=', 'sale')]")
    company_id = fields.Many2one('res.company', string='Company', store=True,
                                 default=lambda self: self.env.company)
    short_code = fields.Char(string='Short Code')
    terms_and_conditions = fields.Text(string='Terms and Conditions')
    product_count = fields.Integer(string='Products',
                                   compute='_compute_product_count')
    subscription_count = fields.Integer(string='Subscriptions',
                                        compute='_compute_subscription_count')
    plan_category_id = fields.Many2one('plan.category', string ="Plan Category")
    choice_count = fields.Integer('Choice Count', compute='_compute_choice_count')
    plan_meal_ids = fields.One2many('plan.meal.line', 'plan_id', string='Available Meals')
    end_date = fields.Date('End Date')
    next_plan_id = fields.Many2one('subscription.package.plan', string='Next Plan', domain="[('id', '!=', id)]")
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, default=lambda self: self.env.company.currency_id)
    plan_price = fields.Float('Price')
    active = fields.Boolean(string='Active', default=True)
    plan_choice_count = fields.Integer(string='Plan Choice', compute='_compute_plan_choice_count')
    meal_config_ids = fields.One2many('choice.config','meal_category_config_id', string='Meal Category')
    additional_meal_config_ids = fields.One2many('choice.config','additional_meal_category_config_id', string='Additional Meal Category')
    day_choice_ids = fields.One2many('plan.choice','plan_config_day_id', string='Days Choices')
    is_ramdan_plan = fields.Boolean('Is Ramdan Plan')
    ramdan_plan_id = fields.Many2one('subscription.package.plan', string='Ramdan Plan')
    inverse_plan_id = fields.Many2one('subscription.package.plan', string='Inverse Plan')

    @api.onchange('protein', 'carbohydrates')
    def _onchange_calories(self):
        for plan in self:
            plan.calories = plan.protein * 4 + plan.carbohydrates * 4


    @api.model
    def default_get(self, fields_list):
        defaults = super(SubscriptionPlan, self).default_get(fields_list)
        meal_lines = []
        meal_category = self.env['meals.category'].search([])
        for meal in meal_category:
            meal_lines.append(
                (0,0,{
                    'meal_category_id': meal.id
                })
            )
        if meal_lines:
            defaults['meal_config_ids'] = meal_lines
        return defaults

    @api.onchange('name')
    def onchange_short_code(self):
        if self.name:
            self.short_code = ''.join([word[0]for word in self.name.split()])
        else:
            self.short_code = False
            
    def _compute_choice_count(self):
        for plan in self:
            choices = self.env['subscription.plan.choice'].search([
                ('plan_id','=',plan.id)
            ])
            plan.choice_count = len(choices)

    def view_choices(self):
        choices = self.env['subscription.plan.choice'].search([
            ('plan_id','=',self.id)
        ])
        action = {
            "name": _("Plan Choices"),
            "type": "ir.actions.act_window",
            "res_model": "subscription.plan.choice",
            "target": "current",
            "context": {
                "default_plan_id": self.id
            }
        }
        if len(choices) > 1:
            action.update({
                "view_mode": "list,form",
                "domain": [('id','=',choices.ids)]
            })
        elif len(choices) == 1:
            action.update({
                "view_mode": "form",
                "res_id": choices[0].id
            })
        else:
            action.update({
                "view_mode": "form",
            })
        return action

    @api.depends('product_count')
    def _compute_product_count(self):
        """ Calculate product count based on subscription plan """
        self.product_count = self.env['product.product'].search_count(
            [('subscription_plan_id', '=', self.id)])

    @api.depends('subscription_count')
    def _compute_subscription_count(self):
        """ Calculate subscription count based on subscription plan """
        self.subscription_count = self.env[
            'diet.subscription.order'].search_count([('plan_id', '=', self.id)])
        
    @api.depends('plan_choice_count')
    def _compute_plan_choice_count(self):
        for plan in self:
            plan.plan_choice_count = self.env['plan.choice'].search_count([('plan_id', '=', plan.id)])


    def button_product_count(self):
        """ It displays products based on subscription plan """
        return {
            'name': 'Products',
            'res_model': 'product.product',
            'domain': [('subscription_plan_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'context': {
                'default_is_subscription': True,'default_is_meal': True,'default_subscription_plan_id' : self.id
            },
        }

    def button_sub_count(self):
        """ It displays subscriptions based on subscription plan """
        return {
            'name': 'Subscriptions',
            'domain': [('plan_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'diet.subscription.order',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def name_get(self):
        """ It displays record name as combination of short code and
        plan name """
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.short_code, rec.name)))
        return res
    
    def generate_recipe(self):
        available_meals =[]
        all_meals = self.env['weekly.meal'].search([('plan_id', '=', self.id)])

        AvailableMeal = self.env['subscription.plan.meals']

        for meal in all_meals:
            ingredient_line_ids = [
                (0, 0, {
                    'ingredient_id': line.ingredient_id.id,
                    'qty': line.quantity,
                    'unit': line.product_uom.id
                }) for line in meal.ingredients_line_ids
            ]

            AvailableMeal.create({'meal_id': meal.id, 'plan_id' : self.id ,
                                    'protein':meal.protein,'carbohydrates':meal.carbohydrates,
                                    "fats":meal.fat,
                                    'recipe_ingredient_line_ids': ingredient_line_ids,
                                    'recipe': meal.recipe})
        else: 
            raise ValidationError(_("Configure meals in plan"))
    
            
    
            
    @api.model_create_multi
    def create(self, vals):
        plan = super(SubscriptionPlan, self).create(vals)
        self.create_service_product(plan)
        return plan

    def create_service_product(self, plan):
        product_data = {
            'name': f"{plan.name}",
            'plan_id' : plan.id,
            'type': 'service',
            'is_plan': True
        }
        new_product = self.env['product.template'].create(product_data)
        return new_product
    
    def service_product(self):
        product_id = self.env['product.template'].search([('plan_id','=',self.id)])
        return {
            'name': 'Service Product',
            'domain': [('plan_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'product.template',
            'res_id':product_id.id,
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
        }
    
    def archive_records(self):
        for rec in self:
            choices_to_archive = rec.env['plan.choice'].search([('plan_id', '=', rec.id),('active', '=', True)])
            choices_to_archive.write({'active': False})

    def unarchive_records(self):
        for rec in self:
            choices_to_unarchive = rec.env['plan.choice'].search([('plan_id', '=', rec.id),('active', '=', False)])
            choices_to_unarchive.write({'active': True})

    def write(self, vals):
        if 'active' in vals and not vals['active']:
            for rec in self:
                rec.archive_records()
                product = self.env['product.template'].search([('plan_id', '=', rec.id), ('active', '=', True)])
                if product:
                    product.write({'active': False})
        else:
            for rec in self:
                rec.unarchive_records()
                product = self.env['product.template'].search([('plan_id', '=', rec.id), ('active', '=', False)])
                if product:
                    product.write({'active': True})
        return super(SubscriptionPlan, self).write(vals)

    @api.constrains('name')
    def _constrains_name(self):
        for plan in self:
            existing_plan_name_query = f"""SELECT name FROM subscription_package_plan WHERE id != {plan.id}"""
            self._cr.execute(existing_plan_name_query)
            existing_plan_names = self._cr.fetchall()
            for name in existing_plan_names:
                if plan.name.lower() == name[0].lower():
                    raise ValidationError(_("Plan name already exists"))
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(SubscriptionPlan, self).unlink()

class PlanMealLine(models.Model):
    _name = 'plan.meal.line'
    _description = 'Plan Meal Line'
    
    plan_id = fields.Many2one('subscription.package.plan', string='Plan')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    protein = fields.Float(string ="Protein")
    carbohydrates = fields.Float(string ="Carbs")
    default_count = fields.Integer('Default Count')
    meal_ids = fields.Many2many('product.template', string='Meal', compute='compute_meal_ids')
    meal_config_id = fields.Many2one('weekly.meal', string='Meal Configuration')
    protein = fields.Float(string ="Protein")
    carbohydrates = fields.Float(string ="Carbs")

  
    def open_weekly_meal_configuration(self):
        action = {
            "name": _(f"Weekly {self.meal_category_id.name if self.meal_category_id else 'Meal'} Configuration"),
            "type": "ir.actions.act_window",
            "res_model": "weekly.meal",
            "view_mode": "form",
            "target": "new",
        }
        if not self.meal_config_id:
            self.meal_config_id = self.env['weekly.meal'].create({
                "plan_meal_line_id": self.id,
            })
        action["res_id"] = self.meal_config_id.id
        return action


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    plan_id = fields.Many2one('subscription.package.plan', string='Plan')


class AddtionalMealSelection(models.Model):
    _name = 'additional.meal.selection'
    _description = 'Additional Meal Selection'

    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    plan_id = fields.Many2one('subscription.package.plan', string='Plan')
    meal_id = fields.Many2one('product.template', string='Meals')
    default_count = fields.Integer('Default Count', default=1)
    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    plan_choice_id = fields.Many2one('plan.choice', string='Plan Choice')
    price = fields.Float('Price/ Day')

    def open_weekly_meal_configuration(self):
        action = {
            "name": _(f"Weekly {self.meal_category_id.name if self.meal_category_id else 'Meal'} Configuration"),
            "type": "ir.actions.act_window",
            "res_model": "weekly.meal",
            "view_mode": "form",
            "target": "new",
        }
        return action