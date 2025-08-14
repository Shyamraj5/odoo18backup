from odoo import models,fields, api
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_price_locked = fields.Boolean(
        string="Is Price Locked",
        related="product_id.is_price_locked"
    )

    @api.onchange('price_unit', 'product_id')
    def _onchange_locked_product(self):
        """
        Automatically set the price from the product if the price is locked.
        """
        if self.product_id and self.product_id.is_price_locked:
            if self.price_unit < self.product_id.list_price:
                raise models.ValidationError(
                        "The price for the product '%s' is locked and cannot be less than locked price %s." % (self.product_id.display_name, self.product_id.list_price)
                    )
            
    @api.constrains('price_unit', 'product_id')
    def _check_locked_product(self):
       for line in self:
            if line.product_id and line.product_id.is_price_locked:
                if line.price_unit < line.product_id.list_price:
                    raise models.ValidationError(
                            "The price for the product '%s' is locked and cannot be less than locked price %s." % (line.product_id.display_name, line.product_id.list_price)
                        )
                
    @api.constrains('price_unit', 'product_template_id')
    def _check_locked_product_template(self):
       for line in self:
            if line.product_template_id and line.product_template_id.is_price_locked:
                if line.price_unit < line.product_template_id.list_price:
                    raise models.ValidationError(
                            "The price for the product '%s' is locked and cannot be less than locked price %s." % (line.product_id.display_name, line.product_id.list_price)
                    )
