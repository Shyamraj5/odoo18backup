from odoo import models, fields, api

class PlanDefaultMeals(models.Model):
    _name = 'plan.default.meals'
    _description = 'Plan Default Meals'
    
    meal_count_line_id = fields.Many2one('choice.config', string='Meal Count Line')
    plan_id = fields.Many2one('subscription.package.plan', string='Plan', related='meal_count_line_id.meal_category_config_id')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='meal_count_line_id.meal_category_id')
    sunday_meal_ids = fields.Many2many('product.template', 'plan_sunday_default_meals_rel', 'plan_default_id', 'meal_id', string='Sunday Default Meals')
    monday_meal_ids = fields.Many2many('product.template', 'plan_monday_default_meals_rel', 'plan_default_id', 'meal_id', string='Monday Default Meals')
    tuesday_meal_ids = fields.Many2many('product.template', 'plan_tuesday_default_meals_rel', 'plan_default_id', 'meal_id', string='Tuesday Default Meals')
    wednesday_meal_ids = fields.Many2many('product.template', 'plan_wednesday_default_meals_rel', 'plan_default_id', 'meal_id', string='Wednesday Default Meals')
    thursday_meal_ids = fields.Many2many('product.template', 'plan_thursday_default_meals_rel', 'plan_default_id', 'meal_id', string='Thursday Default Meals')
    friday_meal_ids = fields.Many2many('product.template', 'plan_friday_default_meals_rel', 'plan_default_id', 'meal_id', string='Friday Default Meals')
    saturday_meal_ids = fields.Many2many('product.template', 'plan_saturday_default_meals_rel', 'plan_default_id', 'meal_id', string='Saturday Default Meals')
