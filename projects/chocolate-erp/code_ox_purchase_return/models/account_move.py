from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    purchase_return_id = fields.Many2one("purchase.return", string="Sale Return")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    purchase_return_line_id = fields.Many2one("purchase.return.line", string="Purchase Return Line")