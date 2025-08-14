from  odoo import models, fields, api


class MealRecipe(models.Model):
    _name = "meal.recipe"
    _description = "Recipe of meals based on carb/protein"


    name = fields.Char(string ="Code", copy =False, readonly =True)
    subscription_plan_id = fields.Many2one('subscription.package.plan', string ="Plan")
    protein = fields.Float(string ="Protein")
    carbohydrates = fields.Float(string ="Carbs")
    recipe = fields.Html(string ="Recipe")
    meal_id = fields.Many2one('product.template', string ="Meal")
    


    @api.model_create_multi
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('recipe.code')
        return super(MealRecipe, self).create(vals)
    
    
    
class SubscriptionPlanMeals(models.Model):
    _name = "subscription.plan.meals"
    _description = "Meals of a Plan"
    
    meal_id = fields.Many2one('product.template', string ="Meal")
    plan_id = fields.Many2one('subscription.package.plan', string ="Plan")
    protein = fields.Float(string ="Protein")
    carbohydrates = fields.Float(string ="Carbs")
    fats = fields.Float(string ="Fat")
    calorie = fields.Float(string ="Calorie", compute='_compute_calorie', store=True)
    recipe = fields.Html(string ="Recipe")
    name = fields.Char(string ="Code", copy =False, readonly =True)
    state = fields.Selection([('draft','Draft'),('completed', 'Completed')], default ='draft', string="State")
    recipe_ingredient_line_ids = fields.One2many('recipe.ingredient.line', 'line_id',string ="Ingredient Lines")
    company_id = fields.Many2one('res.company', string= "Company", default = lambda self: self.env.user.company_id)


    def recipe_print_preview(self):
        return self.env.ref("diet.action_report_meal_recipe_preview").report_action(self, config=False)
    
    def recipe_print_pdf(self):
        return self.env.ref("diet.action_report_meal_recipe_pdf").report_action(self, config=False)
    
    def recipe_print_excel(self):
        return self.env.ref("diet.action_report_meal_recipe_excel").report_action(self, config=False)
    
    @api.depends('protein','carbohydrates','fats')
    def _compute_calorie(self):
        for recipe in self:
            calorie = 0
            if recipe.protein:
                calorie += recipe.protein * 4
            if recipe.carbohydrates:
                calorie += recipe.carbohydrates * 4
            if recipe.fats:
                calorie += recipe.fats * 9
            recipe.calorie = calorie

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.meal_id.name, rec.plan_id.name)))
        return res
    
    @api.model_create_multi
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('recipe.code')
        return super(SubscriptionPlanMeals, self).create(vals)
    
    def recipe_completed(self):
        for rec in self:
            rec.state = 'completed'

class RecipeIngredientLine(models.Model):
    _name = "recipe.ingredient.line"
    _description = "Ingredients of recipe"


    ingredient_id = fields.Many2one('product.template', string ="Ingredient")
    qty = fields.Integer(string ="Quantity")
    unit = fields.Many2one('uom.uom', string ="Unit")
    line_id = fields.Many2one('subscription.plan.meals', string ="Line Id")