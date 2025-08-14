from odoo import fields, models, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_return_id = fields.Many2one("sale.return", string="Sale Return")
    is_return = fields.Boolean("Is Return", default=False, copy=False)


class StockMove(models.Model):
    _inherit = "stock.move"

    sale_return_line_id = fields.Many2one("sale.return.line", string="Sale Return Line")
    is_return = fields.Boolean("Is Return", related="picking_id.is_return")
