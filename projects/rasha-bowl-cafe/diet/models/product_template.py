from odoo import fields, models,api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    is_ingredient = fields.Boolean(string ="Is Ingredient", default=False)
    is_meal = fields.Boolean(string ="Is Meal", default=False)
    is_plan = fields.Boolean(string ="Is Plan", default=False)
    ingredients_line_ids = fields.One2many('meal.ingredient', 'meal_id', string ="Ingredients Line")
    fat = fields.Float(string ="Fat", default=0, tracking=True)
    protein = fields.Float(string ="Protein", default=0, tracking=True)
    carbohydrates = fields.Float(string ="Carb", default=0, tracking=True)
    calories = fields.Float(string ="Calories", default=0, tracking=True)
    meal_description = fields.Text('Meal Description', tracking=True)
    meal_category_id = fields.Many2many('meals.category', string ="Meals Category", tracking=True)
    meal_tag_id = fields.Many2many('meals.tag', string ="Meals Tag", tracking=True)
    tag = fields.Char(string='tag')
    app_right_tag =fields.Char(string='App Right Tag')
    label_title = fields.Char(string='Label Title')
    label_sub_title = fields.Char(string='Label Sub Title')
    kitchen_report = fields.Boolean(string='Include In Kitchen Report')
    can_change_plan = fields.Boolean(string='Can Change Plan?')
    is_from_menu = fields.Boolean(string='Is From Menu')
    is_invisible_in_app =fields.Boolean(string='Is Invisible In App')
    offer_name = fields.Char(string= 'Offer Name')
    sequence_in_app = fields.Char(string='Sequence In App')
    app_dislike_attributes= fields.Char(string='App Dislike Attributes')
    tag_information_ids = fields.One2many('tag.information','product_id',string='Tag Information Ids')
    ingredient_category_id = fields.Many2one('meal.ingredient.category', string='Ingredient Category', tracking=True)
    is_semi_cooked = fields.Boolean(string ="Is Semi Cooked", default =False)
    rating = fields.Selection([
        ('0', '0 Star'),
        ('1', '1 Star'),
        ('2', '2 Star'),
        ('3', '3 Star'),
        ('4', '4 Star'),
        ('5', '5 Star')
    ], string='Rating', compute='_compute_rating',store =True)
    rating_count = fields.Integer('Rating Count', compute='_compute_rating',store =True)
    kitchen_type = fields.Many2one('kitchen.type',string="Kitchen Type", tracking=True)
    recipe = fields.Html(string ="Recipe")
    meal_rating_ids = fields.One2many('meal.customer.rating','meal_id',string='Meal Rating')
    brand_id = fields.Many2one('product.brand', string='Brand')
    plan_ids = fields.Many2many('subscription.package.plan',string="Plans")
    all_days = fields.Boolean(string="All Days")
    sunday = fields.Boolean(string="Sunday")
    monday = fields.Boolean(string="Monday")
    tuesday = fields.Boolean(string="Tuesday")
    wednesday = fields.Boolean(string="Wednesday")
    thursday = fields.Boolean(string="Thursday")
    friday = fields.Boolean(string="Friday")
    saturday = fields.Boolean(string="Saturday")
    available_days = fields.Char('Available Days', compute='_compute_available_days', store=True)
    restrict_double_selection = fields.Boolean(string="Is Restrict Double Selection", default=False)
    show_in_app_menu = fields.Boolean(string="Show In App Menu", default=False)
    has_rating = fields.Boolean(string='Has rating', compute='_compute_has_rating')

    @api.depends('rating')
    def _compute_has_rating(self):
        for meal in self:
            if meal.rating:
                meal.has_rating = True
            else:
                meal.has_rating = False

    @api.depends('sunday','monday','tuesday','wednesday','thursday','friday','saturday')
    def _compute_available_days(self):
        for rec in self:
            days = []
            if rec.sunday:
                days.append('Sunday')
            if rec.monday:
                days.append('Monday')
            if rec.tuesday:
                days.append('Tuesday')
            if rec.wednesday:
                days.append('Wednesday')
            if rec.thursday:
                days.append('Thursday')
            if rec.friday:
                days.append('Friday')
            if rec.saturday:
                days.append('Saturday')
            rec.available_days = ', '.join(days)

    @api.onchange('protein','carbohydrates')
    def _onchange_macros(self):
        calories = 0
        if self.protein:
            calories += self.protein*4
        if self.carbohydrates:
            calories += self.carbohydrates*4
        self.calories = calories

    @api.onchange('all_days')
    def _onchange_all_days(self):
        for rec in self:
            if rec.all_days:
                rec.sunday = True
                rec.monday = True
                rec.tuesday = True
                rec.wednesday = True
                rec.thursday = True
                rec.friday = True
                rec.saturday = True
            elif not rec.all_days:
                rec.sunday = False
                rec.monday = False
                rec.tuesday = False
                rec.wednesday = False
                rec.thursday = False
                rec.friday = False
                rec.saturday = False

    @api.depends('meal_rating_ids')
    def _compute_rating(self):
        for meal in self:
            query1 = f"""SELECT rating,meal_id FROM meal_customer_rating WHERE meal_id = {meal['id']}"""
            self.env.cr.execute(query1)
            rating_ids = meal.env.cr.fetchall()
            if rating_ids:
                rating_avg = (sum([int(rate[0]) for rate in rating_ids]) / len(rating_ids))
                decimal_rating_avg = (rating_avg - int(rating_avg))
                if decimal_rating_avg < 0.5:
                    rating_avg = int(rating_avg)
                else:
                    rating_avg = int(rating_avg)+1
                rating_count = len(rating_ids)
            else:
                rating_avg = '0'
                rating_count = 0
                
            query2 = f"""UPDATE product_template SET rating = {str(rating_avg)},rating_count = {rating_count} WHERE id = {meal['id']} """
            self.env.cr.execute(query2)



    @api.onchange('all_day')
    def _onchange_all_day(self):
        for rec in self:
            if rec.all_day:
                rec.sun_day = True
                rec.mon_day = True
                rec.tues_day = True
                rec.wednes_day = True
                rec.thurs_day = True
                rec.fri_day = True
                rec.satur_day = True
    

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'type' not in vals:
                vals['type'] = 'consu'
            if 'type' in vals and vals['type'] == 'consu':
                if not vals.get('default_code'):
                    if 'is_ingredient' in vals and vals['is_ingredient'] == True:
                        vals['default_code'] = self.env['ir.sequence'].next_by_code('ingredients.code')
                    else:
                        vals['default_code'] = self.env['ir.sequence'].next_by_code('meal.code')
        return super().create(vals_list)

    def write(self,vals):
        result = super().write(vals)
        for rec in self:
            if rec.ingredients_line_ids:
                ingredients =self.search([('is_ingredient','=',True)])
                for lines in rec.ingredients_line_ids:
                    if lines['ingredient_id']:
                        lines.ingredient_id.write({'is_ingredient' :True})
                        if lines.ingredient_id not in ingredients:
                            lines.ingredient_id.default_code = self.env['ir.sequence'].next_by_code('ingredients.code')
    
    def recipe_print_preview(self):
        return self.env.ref("diet.action_report_product_recipe_preview").report_action(self, config=False)
    
    def recipe_print_pdf(self):
        return self.env.ref("diet.action_report_product_recipe").report_action(self, config=False)
    
    def recipe_print_excel(self):
        return self.env.ref("diet.action_report_product_meal_recipe_excel").report_action(self, config=False)

    @api.constrains('name')
    def _constrains_name(self):
        for product in self:
            query = f"""SELECT name->>'en_US' FROM product_template WHERE id != {product.id}"""
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            for name in result:
                if product.name.lower() == name[0].lower():
                    raise ValidationError("Name already exists")

    def unlink(self):
        for product in self:
            if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
            if product.is_ingredient:
                meal_ingredent_lines = self.env['meal.ingredient'].search([('ingredient_id','=',product.id)])
                if meal_ingredent_lines:
                    meals = meal_ingredent_lines.mapped('meal_id').mapped('name')
                    raise ValidationError(_("You cannot delete "+product.name+" as it is being used as ingredient in \n"+'\n'.join(meals)))
        return super().unlink()
    

    @api.onchange('sunday', 'monday', 'tuesday', 'thursday', 'friday', 'saturday', 'all_days')
    def _onchange_days(self):
        default_meals = self.env['plan.default.meals'].search([])

        day_field_map = {
            'sunday': 'sunday_meal_ids',
            'monday': 'monday_meal_ids',
            'tuesday': 'tuesday_meal_ids',
            'thursday': 'thursday_meal_ids',
            'friday': 'friday_meal_ids',
            'saturday': 'saturday_meal_ids'
        }

        for day_field, meal_field in day_field_map.items():
            if self[day_field] == False and self._origin[day_field] == True:
                plan_names = []
                for meal in default_meals:
                    for rec in getattr(meal, meal_field):
                        if rec.name == self.name:
                            plan_names.append(meal.plan_id.name)
                if plan_names:
                    raise ValidationError(
                        f"Please remove the meal '{self.name}' from the default meal for {day_field.capitalize()} It is part of the following plans: {', '.join(plan_names)}"
                    )
      
class MealIngredient(models.Model):
    _name = "meal.ingredient"
    _description = "Calorie details of Ingredients"


    fat = fields.Float(string ="Fat")
    protein = fields.Float(string ="Protein")
    carbohydrates = fields.Float(string ="Carb")
    calories = fields.Float(string ="Calories")
    meal_id = fields.Many2one('product.template', string ="Calorie Id")
    ingredient_id = fields.Many2one('product.template',string='Ingredients', domain =[('is_ingredient','=', True)])
    dislikable = fields.Boolean(string ="Dislikable")
    quantity = fields.Float(string ="Quantity")
    price = fields.Float(string ="Price" ,related ="ingredient_id.list_price")
    product_uom = fields.Many2one('uom.uom', string ="Unit", related='ingredient_id.uom_id')
    is_main_ingredient = fields.Boolean('Main Ingredient')

    @api.constrains('dislikable','is_main_ingredient')
    def check_is_dislikable(self):
        for rec in self:
            if rec.is_main_ingredient == True and rec.dislikable == True:
                raise ValidationError(_("Main ingredient of a meal cannot be dislikable!!!"))
    

class MealCustomerRating(models.Model):
    _name = 'meal.customer.rating'
    _description = 'Meal Customer Rating'
    
    meal_id = fields.Many2one('product.template', string='Meal')
    rating = fields.Selection([
        ('0', '0 Star'),
        ('1', '1 Star'),
        ('2', '2 Star'),
        ('3', '3 Star'),
        ('4', '4 Star'),
        ('5', '5 Star')
    ], string='Rating', default='0')
    partner_id = fields.Many2one('res.partner', string='Partner')
    comments = fields.Char(string="Comment")
    contact_no = fields.Char(string="Contact",related='partner_id.phone')

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(MealCustomerRating, self).unlink()