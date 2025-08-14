from odoo import fields, models, api


class SaleOrderLine(models.Model):
    """Inheriting this model  to add new field."""
    _inherit = 'sale.order.line'

    location_id = fields.Many2one('stock.location',
                                       string='Location',
                                       domain="[('usage','=','internal')]",
                                       help=' Choose the location from'
                                            ' where the product taken from')
    location_domain = fields.Char(compute='_compute_location_domain', store=True)

    @api.depends('lot_id')
    def _compute_location_domain(self):
        for line in self:
            domain = []
            if line.lot_id:
                stock_quants = self.env['stock.quant'].search([('lot_id', '=', line.lot_id.id), ('location_id.usage', '=', 'internal'), 
                                                               ('available_quantity', '>', 0)])
                domain = [('id', 'in', stock_quants.mapped('location_id').ids)]
            line.location_domain = domain