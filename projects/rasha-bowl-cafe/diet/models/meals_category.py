
from odoo import models, fields, _, api
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError

class MealsCategory(models.Model):
    _name = "meals.category"
    _description = "Category of Meals"


    name = fields.Char(string ="Name")
    code = fields.Char(string ="Code", default =lambda self :_('New'), copy =False, readonly =True)
    color = fields.Integer(string = "Color")
    is_snack = fields.Boolean(string ="Is Snack")
    short_code = fields.Char(string="Short Code")
    active = fields.Boolean(string='Active', default=True)
    show_pc_combination_in_report = fields.Boolean(string='Show PC Combination in Report')
    is_ramdan = fields.Boolean('Is Ramdan')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code') or vals['code'] == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('meal.category.code') or _('New')
        return super().create(vals_list)
    
    def name_get(self):
        """ It displays record name as combination of code and
        category name """
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.code, rec.name)))
        return res
    
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.code} - {rec.name}'

    @api.constrains('name')
    def _constrains_name(self):
        for category in self:
            query = f"""SELECT name FROM meals_category WHERE id != {category.id or category._origin.id}"""
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            for name in result:
                if category.name.lower() == name[0].lower():
                    raise ValidationError("Name already exists")
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(MealsCategory, self).unlink()
    

            