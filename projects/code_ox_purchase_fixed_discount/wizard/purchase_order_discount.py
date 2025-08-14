from odoo import models, fields, api, _


class PurchaseOrderDiscount(models.TransientModel):
    _inherit = 'purchase.order.discount'

    discount_type = fields.Selection(
        selection_add=[('pol_fixed_discount', "Fixed Amount On All Order Lines")],
    )

    def action_discount_apply(self):
        self.ensure_one()
        self = self.with_company(self.company_id)
        if self.discount_type == 'pol_discount':
            self.purchase_order_id.order_line.write({'discount': self.discount_percentage*100})
        elif self.discount_type == 'pol_fixed_discount':
            self.purchase_order_id.order_line.write({'discount_fixed': self.discount_amount})
        else:
            self.create_discount_lines()