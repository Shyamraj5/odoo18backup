from odoo import models, fields,api, _
from odoo.exceptions import ValidationError, UserError

class PlanCategory(models.Model):
    _name = "plan.category"
    _description = "Plan Category"
    
    name= fields.Char(string='Name')
    plan_id = fields.Many2many('subscription.package.plan',string='Plans')
    color = fields.Integer(string ="Color")
    image = fields.Binary()
    active = fields.Boolean(string='Archived', default=True)

    def archive_records(self):
        for rec in self:
            plans_to_archive = rec.env['subscription.package.plan'].search([('plan_category_id', '=', self.id),('active', '=', True)])
            choices_to_archive = rec.env['plan.choice'].search([('plan_id', 'in', plans_to_archive.ids),('active', '=', True)])

            plans_to_archive.write({'active': False})
            choices_to_archive.write({'active': False})

    def unarchive_records(self):
        for rec in self:
            plans_to_archive = rec.env['subscription.package.plan'].search([('plan_category_id', '=', self.id),('active', '=', False)])
            choices_to_archive = rec.env['plan.choice'].search([('plan_id', 'in', plans_to_archive.ids),('active', '=', False)])

            plans_to_archive.write({'active': True})
            choices_to_archive.write({'active': True})
    

    def write(self, vals):
        if 'active' in vals and not vals['active']:
            for rec in self:
                rec.archive_records()
        else:
            for rec in self:
                rec.unarchive_records()
        return super(PlanCategory, self).write(vals)

    @api.constrains('name')
    def _constrains_name(self):
        for category in self:
            query = f"""SELECT name FROM plan_category WHERE id != {category.id}"""
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            for name in result:
                if category.name.lower() == name[0].lower():
                    raise ValidationError("Name already exists")
                
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(PlanCategory, self).unlink()