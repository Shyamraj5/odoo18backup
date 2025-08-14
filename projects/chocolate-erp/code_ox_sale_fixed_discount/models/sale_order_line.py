from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    discount_fixed = fields.Monetary(
        string="Discount (Fixed)",
        default=0.0,
        currency_field="currency_id",
        help=(
            "Apply a fixed amount discount to this line. The amount is multiplied by "
            "the quantity of the product."
        ),
    )

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'discount_fixed')
    def _compute_amount(self):
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            is_fixed_discount = False
            if line.discount_fixed > 0:
                base_line['discount'] = line.discount_fixed
                is_fixed_discount = True
            self.env['account.tax'].with_context(is_fixed_discount=is_fixed_discount)._add_tax_details_in_base_line(base_line, line.company_id)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal

    @api.constrains('discount', 'discount_fixed')
    def check_applied_discount(self):
        for line in self:
            if line.discount_fixed and line.discount:
                raise ValidationError("You cannot apply both percentage and fixed discounts on the same line.")
            
    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            "discount_fixed": self.discount_fixed,
            })
        return res