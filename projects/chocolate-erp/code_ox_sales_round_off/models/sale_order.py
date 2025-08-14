from odoo import models, fields, _, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Adding Round-off Button in sale order"

    def action_open_round_off_wizard(self):
        self.ensure_one()
        return {
            'name': _("Round-off"),
            'type': 'ir.actions.act_window',
            'res_model': 'sales.round.off.wizard',
            'view_mode': 'form',
            'target': 'new',
        }