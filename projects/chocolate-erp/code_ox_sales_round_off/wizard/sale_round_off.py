from odoo import models, fields, api, _

class RoundOffWizard(models.TransientModel):
    _name = "sales.round.off.wizard"
    _description = "Wizard for Round-off Button in sale order"

    round_off_value = fields.Float(string="Round-off Amount", required=True)

    def apply_round_off(self):
        active_id = self.env.context.get('active_id')

        if not active_id:
            raise ValueError(_("No active Sale Order found."))
        
        sale_order = self.env['sale.order'].browse(active_id)
        if not sale_order:
            raise ValueError(_("Sale Order not found."))
        
        round_off_product = self.env['product.product'].search([('is_roundoff', '=', True)])

        if round_off_product:
            round_off_product = self.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'product_id': round_off_product.id,
                'price_unit': -self.round_off_value,
                'product_uom_qty': 1,
                'product_uom': round_off_product.uom_id.id,
                'tax_id': [(6, 0, [])],
                'is_round_off': True,
            })

        return {'type': 'ir.actions.act_window_close'}