# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )

    intercompany_purchase_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        compute="_compute_intercompany_purchase_line_id",
        compute_sudo=True,
    )

    def _compute_intercompany_purchase_line_id(self):
        """A One2many would be simpler, but the record rules make unaccesible for
        regular users so the logic doesn't work properly"""
        ids_dict_list = self.env["purchase.order.line"].search_read(
            [("auto_sale_line_id", "in", self.ids)], ["id", "auto_sale_line_id"]
        )
        ids_dict = {d["auto_sale_line_id"][0]: d["id"] for d in ids_dict_list}
        for line in self:
            line.intercompany_purchase_line_id = ids_dict.get(line.id, False)

    @api.model_create_multi
    def create(self, vals_list):
        """Sync lines between an confirmed unlocked purchase and a confirmed unlocked
        sale order"""
        lines = super().create(vals_list)
        allowed_states = self._get_allowed_purchase_order_states()
        for order in lines.order_id.filtered(
            lambda x: x.state == "sale" and x.intercompany_purchase_order_id
        ):
            if order.intercompany_purchase_order_id.sudo().state not in allowed_states:
                raise UserError(
                    _(
                        "You can't change this sale order as the corresponding "
                        "purchase is %(state)s",
                        state=order.state,
                    )
                )
            intercompany_user = (
                order.intercompany_purchase_order_id.sudo().company_id.intercompany_sale_user_id
                or self.env.user
            )
            purchase_lines = []
            for sale_line in lines.filtered(lambda x: x.order_id == order):
                purchase_lines.append(
                    order._prepare_purchase_order_line_data(
                        sale_line,
                        order.intercompany_purchase_order_id.sudo().company_id,
                        order.intercompany_purchase_order_id.sudo(),
                    )
                )
            self.env["purchase.order.line"].with_user(intercompany_user.id).sudo().create(
                purchase_lines
            )
        return lines

    @api.model
    def _get_purchase_sale_line_sync_fields(self):
        """Map purchase line fields to the synced sale line peer"""
        return {
            "product_qty": "product_uom_qty",
        }

    def write(self, vals):
        """Sync values of confirmed unlocked sales"""
        res = super().write(vals)
        sync_map = self._get_purchase_sale_line_sync_fields()
        update_vals = {
            sync_map.get(field): value
            for field, value in vals.items()
            if sync_map.get(field)
        }
        if not update_vals:
            return res
        intercompany_user = (
            self.intercompany_purchase_line_id.sudo().company_id.intercompany_sale_user_id
            or self.env.user
        )
        purchase_lines = self.intercompany_purchase_line_id.with_user(
            intercompany_user.id
        ).sudo()
        if not purchase_lines:
            return res
        closed_purchase_lines = purchase_lines.filtered(
            lambda x: x.state not in self._get_allowed_purchase_order_states()
        )
        if closed_purchase_lines:
            raise UserError(
                _(
                    "The generated purchase orders with reference %(orders)s can't be "
                    "modified. They're either unconfirmed or locked for modifications.",
                    orders=",".join(closed_purchase_lines.order_id.mapped("name")),
                )
            )
        # Update directly the sale order so we can trigger the decreased qty exceptions
        for purchase in purchase_lines.order_id:
            purchase.write(
                {
                    "order_line": [
                        (1, line.id, update_vals)
                        for line in purchase_lines.filtered(lambda x: x.order_id == purchase)
                    ]
                }
            )
        return res

    @api.model
    def _check_intercompany_product(self, dest_user, dest_company):
        if (
            self.product_id.company_id
            and self.product_id.company_id not in dest_user.company_ids
        ):
            raise UserError(
                _(
                    "You cannot create PO from SO because product '%s' "
                    "is not intercompany"
                )
                % self.product_id.name
            )

    def _get_allowed_purchase_order_states(self):
        allowed_states = ["purchase"]
        if self.env.context.get("allow_update_locked_purchases", False):
            allowed_states.append("done")
        return allowed_states
