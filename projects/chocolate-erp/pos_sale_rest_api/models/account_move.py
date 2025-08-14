from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    django_id = fields.Integer('Django Invoice ID')