from odoo import models, fields, api, _


class PurchaseReturnRoundOff(models.TransientModel):
    _name = "purchase.return.round.off"
    _description = "Wizard for Round-off Button in purchase return"

    round_off_amount = fields.Float(string="Round-off Amount", required=True)

    def apply_round_off(self):
        active_id = self.env.context.get('active_id')

        if not active_id:
            raise ValueError(_("No active Purchase Return found."))

        purchase_return = self.env['purchase.return'].browse(active_id)
        if not purchase_return:
            raise ValueError(_("Purchase Return not found."))

        round_off_product = self.env['product.product'].search([('is_roundoff', '=', True)])

        if purchase_return and self.round_off_amount:
            purchase_return.write({
                'return_line_ids': [(0, 0, {
                    'price_unit': -abs(self.round_off_amount),
                    'product_qty': 1,
                    'return_qty': 1,
                    'product_id': round_off_product.id,
                    'tax_ids': [(6,0, [])],
                    'is_roundoff': True

                })]
            })

