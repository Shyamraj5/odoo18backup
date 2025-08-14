from odoo import models, fields, api, _


class SaleOrderDiscount(models.TransientModel):
    _inherit = 'sale.order.discount'

    def _prepare_discount_line_values(self, product, amount, taxes, description=None):
        vals = super()._prepare_discount_line_values(product, amount, taxes, description=description)
        vals['is_discount'] = True
        return vals