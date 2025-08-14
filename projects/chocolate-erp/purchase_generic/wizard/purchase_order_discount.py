from odoo import models


class SaleOrderDiscount(models.TransientModel):
    _inherit = 'purchase.order.discount'

    def prepare_discount_line_values(self, product, amount, taxes, description=None):
        vals = super().prepare_discount_line_values(product, amount, taxes, description=description)
        vals['is_discount'] = True
        return vals