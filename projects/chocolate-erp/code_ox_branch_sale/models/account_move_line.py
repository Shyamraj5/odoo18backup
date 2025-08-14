from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    display_type = fields.Selection(
        selection_add=[
            ('margin', 'Margin')
        ],
        ondelete={'margin': 'cascade'}
    )