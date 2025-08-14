from odoo import models, fields, _, api

class SubscriptionPlanChoice(models.Model):
    _name = 'subscription.plan.choice'
    _description = 'Subscription Plan Choice'

    name = fields.Char('Name')
    plan_id = fields.Many2one('subscription.package.plan', string='Plan', ondelete='restrict')
    meal_category_line_ids = fields.One2many('choice.meal.category.line', 'choice_id', string='Meal Category Line')
    day_count = fields.Integer('Day Count')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    price = fields.Monetary(string='Price', currency_field='currency_id')
   

class ChoiceMealCategoryLine(models.Model):
    _name = 'choice.meal.category.line'
    _description = 'Choice Meal Category Line'

    choice_id = fields.Many2one('subscription.plan.choice', string='Choice')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    price = fields.Float('Price')
    additional_add_price = fields.Float('Additional Meal Add Price')
    additional_remove_price = fields.Float('Additional Meal Remove Price')