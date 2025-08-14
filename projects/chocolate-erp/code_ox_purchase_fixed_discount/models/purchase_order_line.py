from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    discount_fixed = fields.Monetary(
        string="Discount (Fixed)",
        default=0.0,
        currency_field="currency_id",
        help=(
            "Apply a fixed amount discount to this line. The amount is multiplied by "
            "the quantity of the product."
        ),
    )

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'discount_fixed')
    def _compute_amount(self):
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            is_fixed_discount = False
            if line.discount_fixed > 0:
                base_line['discount'] = line.discount_fixed / line.product_qty
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
            
    @api.depends('discount', 'price_unit', 'discount_fixed')
    def _compute_price_unit_discounted(self):
        super()._compute_price_unit_discounted()
        for line in self.filtered(lambda l: l.discount_fixed > 0):
            line.price_unit_discounted = line.price_unit - (line.discount_fixed / line.product_qty)

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        res.update({
            "discount_fixed": self.discount_fixed,
        })
        return res

    def _get_gross_price_unit(self):
        self.ensure_one()
        price_unit = self.price_unit
        if self.discount:
            price_unit = price_unit * (1 - self.discount / 100)
        if self.discount_fixed:
            price_unit = price_unit - (self.discount_fixed / self.product_qty)
        if self.taxes_id:
            qty = self.product_qty or 1
            price_unit = self.taxes_id.compute_all(
                price_unit,
                currency=self.order_id.currency_id,
                quantity=qty,
                rounding_method='round_globally',
            )['total_void']
            price_unit = price_unit / qty
        if self.product_uom.id != self.product_id.uom_id.id:
            price_unit *= self.product_uom.factor / self.product_id.uom_id.factor
        return price_unit

    

