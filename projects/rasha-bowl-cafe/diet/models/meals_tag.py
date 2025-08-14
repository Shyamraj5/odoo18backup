from odoo import models, fields, _ 
from odoo.exceptions import UserError


class MealsTag(models.Model):
    _name = "meals.tag"
    _description = "Type of Meal"


    name = fields.Char(string ="Name")
    color = fields.Integer(string = "Color")
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(MealsTag, self).unlink()