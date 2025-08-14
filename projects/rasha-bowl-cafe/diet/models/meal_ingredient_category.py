from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
        
class MealIngredientCategory(models.Model):
    _name = 'meal.ingredient.category'
    _description = 'Meal Ingredient Category'
    
    name = fields.Char('Name')
    code = fields.Char(string ="Code", default =lambda self :_('New'), copy =False, readonly =True)


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals['code'] == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('ingredients.category.code') or _('New')
        return super().create(vals_list)
    
    def name_get(self):
        """ It displays record name as combination of code and
        category name """
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.code, rec.name)))
        return res

    @api.constrains('name')
    def _constrains_name(self):
        for ingredient_category in self:
            query = f"""SELECT name FROM meal_ingredient_category WHERE id != {ingredient_category.id or ingredient_category._origin.id}"""
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            for name in result:
                if ingredient_category.name.lower() == name[0].lower():
                    raise ValidationError("Name already exists")
                
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(MealIngredientCategory, self).unlink()