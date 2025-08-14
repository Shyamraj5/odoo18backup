from odoo import fields, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_return_id = fields.Many2one("purchase.return", string="Purchase Return")


class StockMove(models.Model):
    _inherit = "stock.move"

    purchase_return_line_id = fields.Many2one("purchase.return.line", string="Purchase Return Line")