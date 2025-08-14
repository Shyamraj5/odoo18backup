from odoo import models, fields, api


class PosOrderType(models.Model):
    _name = 'pos.order.type'
    _inherit = ['pos.load.mixin']

    name = fields.Char(string='POS Order Type')

    @api.model
    def _load_pos_data_fields(self, config_id):
        return ['name']