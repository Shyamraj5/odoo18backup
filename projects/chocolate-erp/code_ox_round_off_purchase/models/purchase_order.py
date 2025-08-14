from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_open_round_off_wizard(self):
        """Open the round off wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Round Off',
            'res_model': 'purchase.round.off.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }
     

    @api.depends('order_line.price_subtotal', 'currency_id', 'company_id', 'total_discount')
    def _compute_tax_totals(self):
        res = super(PurchaseOrder, self)._compute_tax_totals()
        AccountTax = self.env['account.tax']
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type and not x.is_discount and not x.is_roundoff)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )
            if order.total_discount > 0:
                order.tax_totals['discount'] = order.total_discount
            global_discount = sum(order.order_line.filtered(lambda x: x.is_discount == True).mapped('price_subtotal'))
            round_off = sum(order.order_line.filtered(lambda x: x.is_roundoff == True).mapped('price_subtotal'))
            if round_off:
                order.tax_totals['round_off'] = round_off
            order.tax_totals['total_amount_currency'] = order.tax_totals['total_amount_currency'] + global_discount + round_off
            if 'subtotals' in order.tax_totals:
                for subtotal in order.tax_totals['subtotals']:
                    if subtotal.get('name') == 'Untaxed Amount':
                        subtotal['name'] = 'Taxable'
        return res