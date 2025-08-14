from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    source_location_id = fields.Many2one('stock.location', string='Source Location')

    @api.onchange('source_location_id')
    def onchange_source_location_id(self):
        for order in self:
            if order.source_location_id:
                for line in order.order_line:
                    line.location_id = order.source_location_id

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            for picking in order.picking_ids:
                picking.write({
                    'picker_id': picking.location_id.picker_id.id,
                    'is_picker_assigned': True,
                    'checker_id': picking.location_dest_id.supervisor_id.id
                })
            out_of_stock = []
            for line in order.order_line:
                if line.lot_id and line.product_id and line.location_id:
                    quant = self.env['stock.quant'].search([('lot_id', '=', line.lot_id.id), 
                                                            ('location_id', '=', line.location_id.id)])
                    if quant:
                        if quant.available_quantity < line.product_uom_qty:
                            out_of_stock.append(line.product_id.display_name)
                    else:
                        raise UserError(_(f'Stock not available for {line.product_id.display_name}'))
            if out_of_stock:
                raise UserError(_(f'Stock not available for following products {", ".join(out_of_stock)}'))
        return res