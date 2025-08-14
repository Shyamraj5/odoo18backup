from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_closing_session = fields.Boolean(string='Allow closing Session', default=1)

