from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    django_id = fields.Integer()