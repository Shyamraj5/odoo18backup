from odoo import models, fields, api, _


class SaleOrderDiscount(models.TransientModel):
    _inherit = 'sale.order.discount' 

    discount_type = fields.Selection(
        selection_add=[('sol_fixed_discount', "Fixed Amount On All Order Lines")],
    )

    def action_apply_discount(self):
        self.ensure_one()
        self = self.with_company(self.company_id)
        if self.discount_type == 'sol_discount':
            self.sale_order_id.order_line.write({'discount': self.discount_percentage*100})
        elif self.discount_type == 'sol_fixed_discount':
            self.sale_order_id.order_line.write({'discount_fixed': self.discount_amount})
        else:
            self._create_discount_lines()