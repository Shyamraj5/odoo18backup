from odoo import api, models, fields, _


class PlanChoice(models.Model):
    _name = "plan.choice"
    _description = "Plan Choice"
    
    name = fields.Char('Name')
    plan_id = fields.Many2one('subscription.package.plan', string='Subscription Plan')
    recipe_count = fields.Integer(string ="Recipe Count", compute ='_compute_recipe_count')
    subscription_count = fields.Integer(string='Subscriptions',compute='_compute_subscription_count')
    duration_type = fields.Selection([
        ('month', 'Month'),
        ('week', 'Week'),
        ('day', 'Day')
    ], string='Duration Type')
    choices = fields.Selection([
        ('no_weekend', 'No Weekend'),
        ('no_friday', 'No Sunday'),
        ('all_day', 'All Day')
    ], string='Plan Choice')
    no_of_week = fields.Selection([
        ('one_week', '1 Week'),
        ('two_week', '2 Week'),
        ('three_week', '3 Week'),
        ('four_week', '4 Week')
    ], string='No. Of Week')
    no_of_day = fields.Integer(string= "No. Of Day", compute="_compute_no_of_days", store=True)
    choice_config_ids = fields.One2many('choice.config','plan_choice_id', string='Meal Category')
    currency_id = fields.Many2one('res.currency', string='Currency', related='plan_config_day_id.currency_id') 
    plan_price = fields.Monetary(currency_field="currency_id", string='Plan Price')
    strike_through_price = fields.Monetary(currency_field="currency_id", string='Strike Through Price')
    active = fields.Boolean(string='Archived', default=True)
    plan_config_day_id = fields.Many2one('subscription.package.plan', string='Plan Choice config')
    sunday = fields.Boolean(string='Sunday', default=False)
    monday = fields.Boolean(string='Monday', default=False)
    tuesday = fields.Boolean(string='Tuesday', default=False)
    wednesday = fields.Boolean(string='Wednesday', default=False)
    thursday = fields.Boolean(string='Thursday', default=False)
    friday = fields.Boolean(string='Friday', default=False)
    saturday = fields.Boolean(string='Saturday', default=False)
    days = fields.Char(string='Days', compute="_compute_days", store=True)
    show_order = fields.Integer('Show Order', default="0")
    is_strike_through = fields.Boolean(string="Show Strike Through Price In App",default=False)
    tax_ids = fields.Many2many('account.tax', string='Taxes',default=lambda self: self.env.company.account_sale_tax_id)
    plan_tax_amount = fields.Monetary(string='Price Total', currency_field='currency_id',compute='_compute_amount_tax')
    meal_config_ids = fields.One2many('choice.config','plan_choice_id', string='Meal Category',readonly=False)
    addtional_meal_ids = fields.One2many('additional.meal.selection','plan_choice_id', string='Additional Meal',readonly=False)

    @api.depends(
            'sunday',
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday'
            )
    def _compute_days(self):
        for day in self:
            value=[]
            if day.sunday:
                value.append('Sunday')
            if day.monday:
                value.append('Monday')
            if day.tuesday:
                value.append('Tuesday')
            if day.wednesday:
                value.append('wednesday')
            if day.thursday:
                value.append('Thursday')
            if day.friday:
                value.append('Friday')
            if day.saturday:
                value.append('Saturday')
            day.days = ",".join(value)
    
    @api.onchange('choices')
    def plan_available_days(self):
        for rec in self:
            if rec.duration_type != 'day':
                if rec.choices == 'no_weekend':
                    rec.write({
                        'sunday': False,
                        'monday': True,
                        'monday': True,
                        'tuesday': True,
                        'wednesday': True,
                        'thursday': True,
                        'friday': True,
                        'saturday': False,
                    })
                elif rec.choices == 'no_friday':
                    rec.write({
                        'sunday': False,
                        'monday': True,
                        'monday': True,
                        'tuesday': True,
                        'wednesday': True,
                        'thursday': True,
                        'friday': True,
                        'saturday': True,
                    })
                elif rec.choices == 'all_day':
                    rec.write({
                        'sunday': True,
                        'monday': True,
                        'monday': True,
                        'tuesday': True,
                        'wednesday': True,
                        'thursday': True,
                        'friday': True,
                        'saturday': True,
                    })
            else:
                rec.write({
                        'sunday': False,
                        'monday': False,
                        'monday': False,
                        'tuesday': False,
                        'wednesday': False,
                        'thursday': False,
                        'friday': False,
                        'saturday': False,
                    })
                


    @api.onchange('duration_type')
    def onchange_duration_type(self):
        for rec in self:
            if rec.duration_type == 'day':
                rec.choices = None 
                rec.no_of_week = None

    @api.depends('subscription_count')
    def _compute_subscription_count(self):
        """ Calculate subscription count based on subscription plan """
        for subscription in self:
            subscription.subscription_count = self.env['diet.subscription.order'].search_count([
                ('plan_id', '=', subscription.id)
            ])
        
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

    

    def button_recipes(self):
        return {
            'name': 'Recipes',
            'res_model': 'subscription.plan.meals',
            'domain': [('plan_id', '=', self.id)],
            'view_type': 'form',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'context': {'default_plan_id' : self.id},
            }
    
    @api.depends('recipe_count')
    def _compute_recipe_count(self):
        """ Calculate product count based on subscription plan """
        for plan in self:
            plan.recipe_count = self.env['subscription.plan.meals'].search_count([('plan_id', '=', plan.id)])

    @api.depends('duration_type','choices','no_of_week')
    def _compute_no_of_days(self):
        month = 30
        weekands = 8
        fridays = 4
        week = 7
        for rec in self:
            if rec.duration_type == 'month': 
                if rec.choices =='no_weekend':
                    rec.no_of_day = 20
                elif rec.choices =='no_friday':
                    rec.no_of_day = month - fridays
                elif rec.choices =='all_day':
                    rec.no_of_day = month
            elif rec.duration_type == 'week': 
                if rec.choices =='no_weekend' and rec.no_of_week =='one_week':
                    rec.no_of_day = week - (weekands/4)
                elif rec.choices =='no_weekend' and rec.no_of_week =='two_week':
                    rec.no_of_day = 2*(week - (weekands/4))
                elif rec.choices =='no_weekend' and rec.no_of_week =='three_week':
                    rec.no_of_day = 3*(week - (weekands/4))
                elif rec.choices =='no_weekend' and rec.no_of_week =='four_week':
                    rec.no_of_day = 4*(week - (weekands/4))
                elif rec.choices =='no_friday' and rec.no_of_week =='one_week':
                    rec.no_of_day = week - (fridays/4)
                elif rec.choices =='no_friday' and rec.no_of_week =='two_week':
                    rec.no_of_day = 2*(week - (fridays/4))
                elif rec.choices =='no_friday' and rec.no_of_week =='three_week':
                    rec.no_of_day = 3*(week - (fridays/4))
                elif rec.choices =='no_friday' and rec.no_of_week =='four_week':
                    rec.no_of_day = 4*(week - (fridays/4))
                elif rec.choices =='all_day' and rec.no_of_week =='one_week':
                    rec.no_of_day = week 
                elif rec.choices =='all_day' and rec.no_of_week =='two_week':
                    rec.no_of_day = 2*week
                elif rec.choices =='all_day' and rec.no_of_week =='three_week':
                    rec.no_of_day = 3*week 
                elif rec.choices =='all_day' and rec.no_of_week =='four_week':
                    rec.no_of_day = 4*week 
            else:
                rec.no_of_day=1

    @api.depends('plan_price', 'tax_ids')
    def _compute_amount_tax(self):
        for record in self:
            untaxed_amount = record.plan_price
            amount_tax_obj = record.tax_ids.compute_all(untaxed_amount, currency=record.currency_id)
            record.plan_tax_amount = amount_tax_obj['total_included']

class ChoiceConfig(models.Model):
    _name = 'choice.config'
    _description = 'Configure Choice'
    _rec_name = 'meal_category_id'

    sequence = fields.Integer('Sequence', copy=False)
    meal_category_config_id = fields.Many2one('subscription.package.plan', string='Meal Choice config')
    additional_meal_category_config_id = fields.Many2one('subscription.package.plan', string='Additional Meal Choice Config')
    plan_choice_id = fields.Many2one('plan.choice', string='Plan Choice')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    meal_count = fields.Integer(string="Meal Count")
    default_count = fields.Integer('Default Count')
    currency_id = fields.Many2one('res.currency', string='Currency', related='meal_category_config_id.currency_id') 
    additional_price = fields.Monetary(currency_field="currency_id", string='Additional Price')
    plan_default_meal_id = fields.Many2one('plan.default.meals', string='Default Meals')
    calorie_multiply_factor = fields.Float('Calorie Multiply Factor', default=1.0)

    def open_default_meals(self):
        if self.plan_default_meal_id:
            action = {
                "name": _(f"Default Meals"),
                "type": "ir.actions.act_window",
                "res_model": "plan.default.meals",
                "view_mode": "form",
                "target": "new",
            }
            action["res_id"] = self.plan_default_meal_id.id
        else:
            action = {
                "name": _(f"Default Meals"),
                "type": "ir.actions.act_window",
                "res_model": "plan.default.meals",
                "view_mode": "form",
                "target": "new",
            }
            self.plan_default_meal_id = self.env['plan.default.meals'].create({
                "meal_count_line_id": self.id,
            })
            action["res_id"] = self.plan_default_meal_id.id
        return action
