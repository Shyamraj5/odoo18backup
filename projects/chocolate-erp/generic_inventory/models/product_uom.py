from odoo import models, fields, api


class ProductUom(models.Model):
    _name = 'product.uom'
    _description = 'Product Unit of Measure'

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', ondelete='cascade', domain="[('category_id', '=', product_uom_category_id)]")
    list_price = fields.Float(string='Sale Price', digits='Product Price')
    product_id = fields.Many2one('product.product', string='Product', check_company=True, ondelete="cascade")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_uom_ids = fields.Many2many(
        'uom.uom', string="Product UoM", 
        domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='uom_id.category_id')
