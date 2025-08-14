from odoo import _, fields, models, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_return_ids = fields.One2many("sale.return", "sale_order_id", string="Sale Return")
    sale_return_count = fields.Integer("Sale Return Count", compute="_compute_sale_return_count")

    def _compute_sale_return_count(self):
        for rec in self:
            sale_returns = self.sale_return_ids.filtered(lambda sr: sr.state != "cancel")
            if sale_returns:
                rec.sale_return_count = len(sale_returns)
            else:
                rec.sale_return_count = 0

    def open_sale_return(self):
        for rec in self:
            sale_returns = self.sale_return_ids.filtered(lambda sr: sr.state != "cancel")
            if rec.sale_return_count > 1:
                action = {
                    "name": _("Sale Returns"),
                    "type": "ir.actions.act_window",
                    "res_model": "sale.return",
                    "domain": [("id", "in", sale_returns.ids)],
                    "view_mode": "list,form",
                    "target": "current",
                }
            else:
                action = {
                    "name": _("Sale Returns"),
                    "type": "ir.actions.act_window",
                    "res_model": "sale.return",
                    "res_id": sale_returns.ids[0],
                    "view_mode": "form",
                    "target": "current",
                }
        return action

    def create_return(self):
        for rec in self:
            for returns in rec.sale_return_ids:
                stock_picking =rec.env['stock.picking'].search([('sale_return_id','=',returns.id),('state','!=','done')])
                if stock_picking:
                    raise UserError(_(f"Validate receipt of {stock_picking.sale_return_id.name}."))
            delivered_lines = rec.order_line.filtered(lambda oline: oline.qty_delivered > 0)
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
                "sale_order_id": rec.id,
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

    @api.depends("order_line.invoice_lines")
    def _get_invoiced(self):
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda r: r.move_type in ("out_invoice", "out_refund")
            )
            sale_returns = self.sale_return_ids.filtered(lambda sr: sr.state != "cancel")
            if sale_returns and sale_returns.credit_note_ids:
                invoices += sale_returns.mapped("credit_note_ids")
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_returned = fields.Float("Qty Returned", default=0.0, copy=False)
