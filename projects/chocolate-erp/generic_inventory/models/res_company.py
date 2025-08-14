from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    allowed_user_ids = fields.Many2many(
        'res.users',
        string="Users"
    )