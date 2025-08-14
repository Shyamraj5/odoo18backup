from odoo import models, fields, _ 
from odoo.exceptions import UserError

class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'
    
    name = fields.Char('Name')

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(ProductBrand, self).unlink()