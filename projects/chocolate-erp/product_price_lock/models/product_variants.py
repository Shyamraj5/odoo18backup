from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_price_locked = fields.Boolean(string='Price Locked', default=False)

    def toggle_price_lock(self):
        """
        Toggle the price lock status
        """
        for variant in self:
            variant.is_price_locked = not variant.is_price_locked

    def lock_product_prices(self):
        """
        Lock the prices for selected products
        """
        for product in self:
            if not product.is_price_locked:
                product.is_price_locked = True
            else:
                raise UserError("The price is already locked for this product.")
                
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
