from odoo import models, fields, api

class PurchaseRoundOffWizard(models.TransientModel):
    _name = "purchase.round.off.wizard"
    _description = "Round Off Wizard"

    round_off_amount = fields.Float("Round Off Amount")

    def apply_round_off(self):
        """Apply round off amount to purchase order lines."""
        order_id = self.env.context.get('active_id')
        order = self.env['purchase.order'].browse(order_id)

        if order and self.round_off_amount:
            # Check for an existing product or create a new one
            product = self.env['product.product'].search([('is_roundoff', '=', True)], limit=1)
            # Add the round-off amount as a new purchase order line
            order.write({
                'order_line': [(0, 0, {
                    'name': 'Round Off',
                    'price_unit': -abs(self.round_off_amount),
                    'product_qty': 1,
                    'product_id': product.id,
                    'taxes_id': [(6,0, [])],
                    'is_roundoff': True

                })]
            })

