from odoo import models, fields, Command
from contextlib import ExitStack, contextmanager


class AccountMove(models.Model):
    _inherit = 'account.move'

    inter_company = fields.Boolean(default=False)