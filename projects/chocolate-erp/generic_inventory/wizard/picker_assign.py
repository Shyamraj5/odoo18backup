from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPickingPickerAssign(models.TransientModel):
    _name = 'stock.picking.picker.assign'
    _description = 'Assign Picker to Stock Picking'

    picker_id = fields.Many2one('res.users', string="Picker")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    picker_domain = fields.Binary(compute='_compute_picker_domain')

    @api.depends('picking_id')
    def _compute_picker_domain(self):
        for rec in self:
            rec.picker_domain = [('id', 'in', [])]
            if rec.picking_id.location_id and rec.picking_id.location_id.picker_id:
                rec.picker_domain = [('id', 'in', rec.picking_id.location_id.picker_id.ids)]

    def assign_picker(self):
        if self.picking_id and self.picker_id:
            if not self.picking_id.location_dest_id.supervisor_id:
                raise UserError(_('Please set Checker for location'))
            self.picking_id.write({
                'picker_id': self.picker_id.id,
                'checker_id': self.picking_id.location_dest_id.supervisor_id.id,
                'is_picker_assigned': True
            })
            task_lines = []
            for move in self.picking_id.move_ids_without_package:
                task_lines.append((0, 0, {
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'quantity': move.product_uom_qty,
                    'uom_id': move.product_uom.id,
                }))
            picking_task_vals = {
                'picker_id': self.picker_id.id,
                'checker_id': self.picking_id.location_id.supervisor_id.id,
                'picking_id': self.picking_id.id,
                'line_ids': task_lines
            }
            self.env['stock.picking.picker.task'].create(picking_task_vals)
