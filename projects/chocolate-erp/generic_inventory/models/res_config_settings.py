from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allowed_user_ids = fields.Many2many(
        'res.users',
        related='company_id.allowed_user_ids',
        readonly=False,
    )
