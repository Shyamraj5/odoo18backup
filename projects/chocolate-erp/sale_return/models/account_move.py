from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools.translate import _


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_return_id = fields.Many2one("sale.return", string="Sale Return")

    

    def create_return(self):
        for rec in self:
            source_orders = self.line_ids.sale_line_ids.order_id
            for returns in source_orders.sale_return_ids:
                stock_picking = rec.env['stock.picking'].search([
                    ('sale_return_id', '=', returns.id),
                    ('state', '!=', 'done')
                ])
                if stock_picking:
                    raise UserError(_(f"Validate receipt of {stock_picking.sale_return_id.name}."))
            delivered_lines = source_orders.order_line.filtered(lambda oline: oline.qty_delivered > 0)
            if not delivered_lines:
                raise UserError(_("Deliver some goods to create return."))
            return_lines = []
            for order_line in delivered_lines.filtered(lambda oline: oline.qty_delivered > 0):
                if order_line.product_id.tracking != "none":
                    move_ids = self.env["stock.move"].search(
                        [
                            ("sale_line_id", "=", order_line.id),
                            ("product_id", "=", order_line.product_id.id),
                        ]
                    )
                    if move_ids:
                        move_line_ids = move_ids.move_line_ids.filtered(lambda mline: mline.quantity > 0)
                        available_lot_ids = []
                        for lot in move_line_ids.mapped("lot_id"):
                            in_stock = self.env["stock.quant"].search(
                                [("lot_id", "=", lot.id), ("quantity", ">", 0),]
                            )
                            if in_stock:
                                available_lot_ids.append((4, lot.id))
                    else:
                        available_lot_ids = False
                else:
                    available_lot_ids = False
                return_line = {
                    "product_id": order_line.product_id.id,
                    "name": order_line.name,
                    "quantity": order_line.qty_delivered,
                    "uom_id": order_line.product_uom.id,
                    "sale_order_line_id": order_line.id,
                    "available_lot_ids": available_lot_ids,
                    "lot_ids": available_lot_ids,
                }
                return_lines.append((0, 0, return_line))

            return_vals = {
                "sale_order_id": source_orders.id,
                "partner_id": rec.partner_id.id,
            }
            sale_return = self.env['sale.return'].create(return_vals)

        return {
            "name": _("Sale Return"),
            "type": "ir.actions.act_window",
            "res_model": "sale.return",
            # "context": return_vals,
            "res_id": sale_return.id,
            "view_mode": "form",
            "target": "current",
        }

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sale_return_line_id = fields.Many2one("sale.return.line", string="Sale Return Line")
