from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_fixed = fields.Monetary(
        string="Discount (Fixed)",
        default=0.0,
        currency_field="currency_id",
        help=(
            "Apply a fixed amount discount to this line. The amount is multiplied by "
            "the quantity of the product."
        ),
    )

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'discount_fixed')
    def _compute_totals(self):
        """ Compute 'price_subtotal' / 'price_total' outside of `_sync_tax_lines` because those values must be visible for the
        user on the UI with draft moves and the dynamic lines are synchronized only when saving the record.
        """
        AccountTax = self.env['account.tax']
        for line in self:

            # TODO remove the need of cogs lines to have a price_subtotal/price_total
            if line.display_type not in ('product', 'cogs'):
                line.price_total = line.price_subtotal = False
                continue

            base_line = line.move_id._prepare_product_base_line_for_taxes_computation(line)
            is_fixed_discount = False
            if line.discount_fixed > 0:
                base_line['discount'] = (line.discount_fixed / line.quantity) if line.move_type in ('in_invoice', 'in_refund') else line.discount_fixed
                is_fixed_discount = True
            AccountTax.with_context(is_fixed_discount=is_fixed_discount)._add_tax_details_in_base_line(base_line, line.company_id)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']

    @api.depends('quantity', 'price_unit', 'price_subtotal', 'is_discount', 'discount_fixed')
    def _compute_discount_amount(self):
        super()._compute_discount_amount()
        for line in self.filtered(lambda x: x.discount_fixed > 0):
            line.discount_amount = (line.quantity * line.price_unit) - line.price_subtotal