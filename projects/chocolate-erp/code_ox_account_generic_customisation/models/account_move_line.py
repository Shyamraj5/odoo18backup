from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_discount = fields.Boolean(string='Is Discount', default=False)
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount_amount', store=True)
    price_tax = fields.Float(compute='_compute_tax_amount', string='Tax', store=True)
    is_roundoff = fields.Boolean(string="Round Off", default=False)

    @api.depends('quantity', 'price_unit', 'price_subtotal', 'is_discount')
    def _compute_discount_amount(self):
        for line in self:
            line.discount_amount = 0
            if line.discount:
                line.discount_amount = (line.quantity * line.price_unit) - line.price_subtotal
            if line.is_discount:
                line.discount_amount = -1 * line.price_subtotal

    @api.depends('price_total', 'price_subtotal')
    def _compute_tax_amount(self):
        for line in self:
            line.price_tax = line.price_total - line.price_subtotal