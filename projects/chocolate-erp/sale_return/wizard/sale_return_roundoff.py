from odoo import  fields, models, api
class SaleReturnRoundOffWizard(models.TransientModel):
    _name = 'sale.return.roundoff.wizard'
    _description = 'Sale Return Round Off Wizard'

    roundoff_amount = fields.Float(string="Round Off Amount")

    def apply_roundoff(self):
        order_id = self.env.context.get('active_id')
        order = self.env['sale.return'].browse(order_id)

        if order and self.roundoff_amount:
            # Check for an existing product or create a new one
            product = self.env['product.product'].search([('is_roundoff', '=', True)], limit=1)
            # Add the round-off amount as a new purchase order line
            order.sudo().write({
                'return_line_ids': [(0, 0, {
                    'unit_price': -self.roundoff_amount,
                    'quantity': 1,
                    'product_id': product.id,
                    'tax_id': [(6,0, [])],
                    'is_roundoff': True

                })]
            })
