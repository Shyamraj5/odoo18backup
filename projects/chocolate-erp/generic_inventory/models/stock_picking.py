from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picker_id = fields.Many2one('res.users', string="Picker")
    picker_domain = fields.Binary(compute='_compute_picker_domain')
    is_picker_assigned = fields.Boolean(default=False)
    task_state = fields.Selection([('picker_pending', 'Picker Pending'), ('picker_done', 'Picker Done'), 
                               ('checker_verified', 'Checker Verified'), ('reassigned', 'Re Assigned')],
                               default='picker_pending', compute='_compute_task_state', store=True)
    checker_id = fields.Many2one('res.users', string='Checker')
    is_reassigned = fields.Boolean(default=False)
    grn_received = fields.Boolean(default=False)

    @api.depends('move_ids_without_package.task_state')
    def _compute_task_state(self):
        for picking in self:
            task_states = picking.move_ids_without_package.mapped('task_state')
            if task_states and all(state == 'picker_done' for state in task_states):
                picking.task_state = 'picker_done'
            elif task_states and all(state == 'checker_verified' for state in task_states):
                picking.task_state = 'checker_verified'
            elif task_states and any(state == 'reassigned' for state in task_states):
                picking.task_state = 'reassigned'
            elif task_states and any(state == 'picker_pending' for state in task_states):
                picking.task_state = 'picker_pending'

    @api.depends('location_id')
    def _compute_picker_domain(self):
        for rec in self:
            rec.picker_domain = [('id', 'in', [])]
            if rec.location_id and rec.location_id.picker_id:
                rec.picker_domain = [('id', 'in', rec.location_id.picker_id.ids)]

    def assign_picker(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Picker',
            'res_model': 'stock.picking.picker.assign',
            'view_mode': 'form',
            'view_id': self.env.ref('generic_inventory.view_picker_assign_form').id,
            'target': 'new',
            'context': {'default_picking_id': self.id}
        }