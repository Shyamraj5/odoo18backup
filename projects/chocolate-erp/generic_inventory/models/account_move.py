from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    incoming_picking_count = fields.Integer("Incoming Shipment count", compute='_compute_incoming_picking_count')
    picking_ids = fields.Many2many('stock.picking', string="Picking Ids")

    def action_view_picking(self):
        source_orders = self.line_ids.purchase_line_id.order_id
        return source_orders._get_action_view_picking(self.picking_ids)
    
    @api.depends('line_ids')
    def _compute_incoming_picking_count(self):
        self.incoming_picking_count = len(self.picking_ids)