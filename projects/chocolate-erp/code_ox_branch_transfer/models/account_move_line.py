from odoo import models, fields, api, _, Command
from odoo.tools import frozendict
from contextlib import contextmanager

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_margin = fields.Boolean(default=False)
    invoice_line_ids = fields.One2many(  # /!\ invoice_line_ids is just a subset of line_ids.
        'account.move.line',
        'move_id',
        string='Invoice lines',
        copy=False,
        domain=[('display_type', 'in', ('product', 'line_section', 'line_note')), ('is_margin', '!=', True)],
    )