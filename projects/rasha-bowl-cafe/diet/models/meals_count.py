from odoo import models, fields, api


class MealsCount(models.Model):
    _name = "meals.count"
    _description = "Meals count"

    meal_subscription_id = fields.Many2one('diet.subscription.order')
    ramdan_subscription_id = fields.Many2one('diet.subscription.order')
    meal_category_id = fields.Many2one('meals.category',string ="Meal Category")
    base_meal_count = fields.Integer(string ="Base Meal Count")
    currency_id = fields.Many2one('res.currency', string='Currency', related='meal_subscription_id.currency_id') 
    additional_price = fields.Monetary(currency_field="currency_id", string='Additional Price')
    additional_count = fields.Integer(string="Meal Count")
    sub_total = fields.Monetary(currency_field="currency_id", string="Sub Total",compute='_compute_sub_total')
    additional_meal = fields.Boolean(default=False)
    calorie_multiply_factor = fields.Float('Calorie Multiply Factor', default=1.0, compute='_compute_calorie_multiply_factor')
    is_ramdan = fields.Boolean('Is Ramdan')
    @api.depends(
        'meal_subscription_id.plan_id.meal_config_ids.calorie_multiply_factor',
        'meal_subscription_id.plan_id.additional_meal_config_ids.calorie_multiply_factor',
        'meal_category_id'
    )
    def _compute_calorie_multiply_factor(self):
        for record in self:
            multiplier = 1.0
            if record.meal_subscription_id.plan_id and record.meal_subscription_id.plan_id.meal_config_ids:
                plan_meal_config_id = record.meal_subscription_id.plan_id.meal_config_ids.filtered(lambda config: config.meal_category_id == record.meal_category_id)
                if plan_meal_config_id:
                    multiplier = plan_meal_config_id.calorie_multiply_factor or 1.0
            elif record.meal_subscription_id.plan_id and record.meal_subscription_id.plan_id.additional_meal_config_ids:
                plan_meal_config_id = record.meal_subscription_id.plan_id.additional_meal_config_ids.filtered(lambda config: config.meal_category_id == record.meal_category_id)
                if plan_meal_config_id:
                    multiplier = plan_meal_config_id.calorie_multiply_factor or 1.0
            record.calorie_multiply_factor = multiplier

    @api.depends('additional_count')
    def _compute_sub_total(self):
        total_default_count = sum(self.meal_subscription_id.meal_count_ids.mapped('base_meal_count'))
        total_additional_count = sum(self.meal_subscription_id.meal_count_ids.mapped('additional_count'))
        for meals_count in self:
            meals_count.sub_total = 0
            meals_count_ids = []
            for rec in meals_count.meal_subscription_id.meal_count_ids:
                meals_count_ids.append(rec.id)
                default_count = sum(self.meal_subscription_id.meal_count_ids.filtered(lambda x: x.id in meals_count_ids).mapped('base_meal_count'))
                additional_count = sum(self.meal_subscription_id.meal_count_ids.filtered(lambda x: x.id in meals_count_ids).mapped('additional_count'))
                if default_count >= additional_count:
                    meal_count = 0
                else:
                    diff = total_additional_count - total_default_count
                    meal_count = rec.additional_count - rec.base_meal_count if rec.additional_count > rec.base_meal_count else 0
                    if meal_count > diff:
                        meal_count = meal_count - diff
                rec.update({'sub_total': meal_count * rec.additional_price})