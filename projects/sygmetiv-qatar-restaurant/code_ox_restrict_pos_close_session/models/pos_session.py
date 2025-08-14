from odoo import fields, models, api


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    enable_closure_validation = fields.Boolean("Enable Manager Validation for POS Session Closure",)
