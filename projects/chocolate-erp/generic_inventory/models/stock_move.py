from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    task_state = fields.Selection([('picker_pending', 'Picker Pending'), ('picker_done', 'Picker Done'),
                                   ('checker_verified', 'Checker Verified'), ('reassigned', 'Re Assigned')],
                                   default='picker_pending')
    reassign_reason = fields.Text(string='Re Assing Reason')
    reassign_qty = fields.Float(string='Re Assign Qty')
    reassign_qty_done = fields.Float(string='Re Assign Qty Done')