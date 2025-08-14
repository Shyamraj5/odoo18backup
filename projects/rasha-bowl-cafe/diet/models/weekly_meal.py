from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WeeklyMeal(models.Model):
    _name = 'weekly.meal'
    _description = 'Weekly Meal'
    
    plan_meal_line_id = fields.Many2one('choice.config', string='Plan Choice Meal Line')
    plan_id = fields.Many2one('subscription.package.plan', string='Plan', related='plan_meal_line_id.plan_choice_id.plan_id')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='plan_meal_line_id.meal_category_id')
    default_count = fields.Integer('Default Count', related='plan_meal_line_id.default_count')
    sunday_meal_ids = fields.One2many('sunday.meal.line', 'weekly_meal_id', string='Sunday')
    monday_meal_ids = fields.One2many('monday.meal.line', 'weekly_meal_id', string='Monday')
    tuesday_meal_ids = fields.One2many('tuesday.meal.line', 'weekly_meal_id', string='Tuesday')
    wednesday_meal_ids = fields.One2many('wednesday.meal.line', 'weekly_meal_id', string='Wednesday')
    thursday_meal_ids = fields.One2many('thursday.meal.line', 'weekly_meal_id', string='Thursday')
    friday_meal_ids = fields.One2many('friday.meal.line', 'weekly_meal_id', string='Friday')
    saturday_meal_ids = fields.One2many('saturday.meal.line', 'weekly_meal_id', string='Saturday')
    plan_choices = fields.Selection(related='plan_meal_line_id.plan_choice_id.choices', string="Plan meal line plan")
    

class SundayMealLine(models.Model):
    _name = 'sunday.meal.line'
    _description = 'Sunday Meal Line'
    _order = 'sequence asc'
    
    sequence = fields.Integer('Sequence')
    weekly_meal_id = fields.Many2one('weekly.meal', string='Weekly Meal')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='weekly_meal_id.meal_category_id')
    meal_id = fields.Many2one('product.template', string='Meal')

    @api.constrains('sequence')
    def check_unique_sequence(self):
        for rec in self:
            sequence_record = self.search([('weekly_meal_id','=',rec.weekly_meal_id.id),('meal_category_id','=',rec.meal_category_id.id),('sequence','=',rec.sequence)])
            if len(sequence_record) > 1 :
                raise ValidationError(_("Sequence must be unique!!!"))


class MondayMealLine(models.Model):
    _name = 'monday.meal.line'
    _description = 'Monday Meal Line'
    _order = 'sequence asc'
    
    sequence = fields.Integer('Sequence')
    weekly_meal_id = fields.Many2one('weekly.meal', string='Weekly Meal')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='weekly_meal_id.meal_category_id')
    meal_id = fields.Many2one('product.template', string='Meal')

    @api.constrains('sequence')
    def check_unique_sequence(self):
        for rec in self:
            sequence_record = self.search([('weekly_meal_id','=',rec.weekly_meal_id.id),('meal_category_id','=',rec.meal_category_id.id),('sequence','=',rec.sequence)])
            if len(sequence_record) > 1 :
                raise ValidationError(_("Sequence must be unique!!!"))

class TuesdayMealLine(models.Model):
    _name = 'tuesday.meal.line'
    _description = 'Tuesday Meal Line'
    _order = 'sequence asc'
    
    sequence = fields.Integer('Sequence')
    weekly_meal_id = fields.Many2one('weekly.meal', string='Weekly Meal')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='weekly_meal_id.meal_category_id')
    meal_id = fields.Many2one('product.template', string='Meal')

    @api.constrains('sequence')
    def check_unique_sequence(self):
        for rec in self:
            sequence_record = self.search([('weekly_meal_id','=',rec.weekly_meal_id.id),('meal_category_id','=',rec.meal_category_id.id),('sequence','=',rec.sequence)])
            if len(sequence_record) > 1 :
                raise ValidationError(_("Sequence must be unique!!!"))

class WednesdayMealLine(models.Model):
    _name = 'wednesday.meal.line'
    _description = 'Wednesday Meal Line'
    _order = 'sequence asc'
    
    sequence = fields.Integer('Sequence')
    weekly_meal_id = fields.Many2one('weekly.meal', string='Weekly Meal')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='weekly_meal_id.meal_category_id')
    meal_id = fields.Many2one('product.template', string='Meal')

    @api.constrains('sequence')
    def check_unique_sequence(self):
        for rec in self:
            sequence_record = self.search([('weekly_meal_id','=',rec.weekly_meal_id.id),('meal_category_id','=',rec.meal_category_id.id),('sequence','=',rec.sequence)])
            if len(sequence_record) > 1 :
                raise ValidationError(_("Sequence must be unique!!!"))

class ThursdayMealLine(models.Model):
    _name = 'thursday.meal.line'
    _description = 'Thursday Meal Line'
    _order = 'sequence asc'
    
    sequence = fields.Integer('Sequence')
    weekly_meal_id = fields.Many2one('weekly.meal', string='Weekly Meal')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='weekly_meal_id.meal_category_id')
    meal_id = fields.Many2one('product.template', string='Meal')

    @api.constrains('sequence')
    def check_unique_sequence(self):
        for rec in self:
            sequence_record = self.search([('weekly_meal_id','=',rec.weekly_meal_id.id),('meal_category_id','=',rec.meal_category_id.id),('sequence','=',rec.sequence)])
            if len(sequence_record) > 1 :
                raise ValidationError(_("Sequence must be unique!!!"))

class FridayMealLine(models.Model):
    _name = 'friday.meal.line'
    _description = 'Friday Meal Line'
    _order = 'sequence asc'
    
    sequence = fields.Integer('Sequence')
    weekly_meal_id = fields.Many2one('weekly.meal', string='Weekly Meal')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='weekly_meal_id.meal_category_id')
    meal_id = fields.Many2one('product.template', string='Meal')

    @api.constrains('sequence')
    def check_unique_sequence(self):
        for rec in self:
            sequence_record = self.search([('weekly_meal_id','=',rec.weekly_meal_id.id),('meal_category_id','=',rec.meal_category_id.id),('sequence','=',rec.sequence)])
            if len(sequence_record) > 1 :
                raise ValidationError(_("Sequence must be unique!!!"))

class SaturdayMealLine(models.Model):
    _name = 'saturday.meal.line'
    _description = 'Saturday Meal Line'
    _order = 'sequence asc'
    
    sequence = fields.Integer('Sequence')
    weekly_meal_id = fields.Many2one('weekly.meal', string='Weekly Meal')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', related='weekly_meal_id.meal_category_id')
    meal_id = fields.Many2one('product.template', string='Meal')

    @api.constrains('sequence')
    def check_unique_sequence(self):
        for rec in self:
            sequence_record = self.search([('weekly_meal_id','=',rec.weekly_meal_id.id),('meal_category_id','=',rec.meal_category_id.id),('sequence','=',rec.sequence)])
            if len(sequence_record) > 1 :
                raise ValidationError(_("Sequence must be unique!!!"))

