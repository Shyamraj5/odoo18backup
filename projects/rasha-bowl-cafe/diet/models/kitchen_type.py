from odoo import fields,models, _ 
from odoo.exceptions import UserError

class KitchenType(models.Model):
    _name = "kitchen.type"
    _description = "Kitchen Type"

    name = fields.Char(string="Name")

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(KitchenType, self).unlink()