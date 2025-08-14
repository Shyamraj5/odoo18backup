from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPickingPickerTask(models.Model):
    _name = 'stock.picking.picker.task'
    _description = 'Picker Task'

    picker_id = fields.Many2one('res.users', string="Picker")
    checker_id = fields.Many2one('res.users', string='Checker')
    picking_id = fields.Many2one('stock.picking', string="Picking")
    location_id = fields.Many2one('stock.location', related='picking_id.location_id')
    location_dest_id = fields.Many2one('stock.location', related='picking_id.location_dest_id')
    state = fields.Selection([('assigned', 'Assigned'), ('done', 'Done'), ('verified', 'Verified')], default='assigned')
    line_ids = fields.One2many('stock.picking.picker.task.line', 'task_id')


class StockPickingPickerTaskLine(models.Model):
    _name = 'stock.picking.picker.task.line'
    _description = 'Picker Task Line'

    move_id = fields.Many2one('stock.move', string='Stock Move')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='UoM')
    task_id = fields.Many2one('stock.picking.picker.task')
    expiry_date = fields.Datetime(string='Expiry Date')
    state = fields.Selection([('assigned', 'Assigned'), ('done', 'Done'), ('verified', 'Verified'), ('reassigned', 'Re assigned')], default='assigned')
