# Copyright 2013-Today Odoo SA
# Copyright 2016-2019 Chafique DELLI @ Akretion
# Copyright 2018-2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    auto_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Source Purchase Order",
        readonly=True,
        copy=False,
    )
    intercompany_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        compute="_compute_intercompany_purchase_order_id",
        compute_sudo=True,
    )
    inter_company = fields.Boolean(default=False)

    def _compute_intercompany_purchase_order_id(self):
        """A One2many would be simpler, but the record rules make unaccesible for
        regular users so the logic doesn't work properly"""
        ids_dict_list = self.env["purchase.order"].search_read(
            [("auto_sale_order_id", "in", self.ids)],
            ["id", "auto_sale_order_id"],
        )
        ids_dict = {d["auto_sale_order_id"][0]: d["id"] for d in ids_dict_list}
        for order in self:
            order.intercompany_purchase_order_id = ids_dict.get(order.id, False)

    def action_confirm(self):
        if self.env.context.get('so_from_po'):
            for order in self.filtered("auto_purchase_order_id"):
                for line in order.order_line.sudo():
                    if line.auto_purchase_line_id:
                        line.auto_purchase_line_id.price_unit = line.price_unit
        res = super().action_confirm()
        self = self.sudo()
        dest_company = (
            self.partner_id.commercial_partner_id.ref_company_ids
        )
        if dest_company and dest_company.so_from_po:
            self.inter_company = True
            self.with_company(dest_company.id)._inter_company_create_purchase_order(dest_company)
        return res
    
    def _check_intercompany_product(self, dest_company):
        domain = self._get_user_domain(dest_company)
        dest_user = self.env["res.users"].search(domain, limit=1)
        if dest_user:
            for sale_line in self.order_line:
                sale_line._check_intercompany_product(dest_user, dest_company)

    def _get_user_domain(self, dest_company):
        self.ensure_one()
        group_purchase_user = self.env.ref("purchase.group_purchase_user")
        return [
            ("id", "!=", 1),
            ("company_id", "=", dest_company.id),
            ("id", "in", group_purchase_user.users.ids),
        ]
    
    def _inter_company_create_purchase_order(self, dest_company):
        """Create a Purchase Order from the current SO (self)
        Note : In this method, reading the current SO is done as sudo,
        and the creation of the derived
        PO as intercompany_user, minimizing the access right required
        for the trigger user.
        :param dest_company : the company of the created SO
        :rtype dest_company : res.company record
        """
        self.ensure_one()
        # Check intercompany user
        intercompany_user = dest_company.intercompany_sale_user_id
        if not intercompany_user:
            intercompany_user = self.env.user
        # check intercompany product
        self._check_intercompany_product(dest_company)
        # Accessing to selling partner with selling user, so data like
        # property_account_position can be retrieved
        company_partner = self.company_id.partner_id
        # check pricelist currency should be same with PO/SO document
        if self.currency_id.id != (
            company_partner.property_product_pricelist.currency_id.id
        ):
            raise UserError(
                (
                    "You cannot create PO from SO because "
                    "purchase price list currency is different than "
                    "sale price list currency."
                )
            )
        # create the SO and generate its lines from the PO lines
        purchase_order_data = self._prepare_purchase_order_data(
            self.name, company_partner, dest_company, False
        )
        purchase_order = (
            self.env["purchase.order"]
            .with_user(intercompany_user.id)
            .sudo()
            .create(purchase_order_data)
        )
        for sale_line in self.order_line:
            purchase_line_data = self._prepare_purchase_order_line_data(
                sale_line, dest_company, purchase_order
            )
            self.env["purchase.order.line"].with_user(intercompany_user.id).sudo().create(
                purchase_line_data
            )
        # write supplier reference field on PO
        if not self.client_order_ref:
            self.client_order_ref = purchase_order.name
        # Validation of sale order
        if dest_company.sale_auto_validation:
            context = {'po_from_so': True}
            purchase_order.with_user(intercompany_user.id).with_context(context).sudo().button_approve()

    def _prepare_purchase_order_data(
        self, name, partner, dest_company, direct_delivery_address
    ):
        """Generate the Purchase Order values from the SO
        :param name : the origin client reference
        :rtype name : string
        :param partner : the partner reprenseting the company
        :rtype partner : res.partner record
        :param dest_company : the company of the created SO
        :rtype dest_company : res.company record
        :param direct_delivery_address : the address of the SO
        :rtype direct_delivery_address : res.partner record
        """
        self.ensure_one()
        delivery_address = direct_delivery_address or partner or False
        new_order = self.env["purchase.order"].new(
            {
                "company_id": dest_company.id,
                "partner_ref": name,
                "partner_id": partner.id,
                "date_order": self.date_order,
                "auto_sale_order_id": self.id,
                "inter_company": True,
            }
        )
        for onchange_method in new_order._onchange_methods["partner_id"]:
            onchange_method(new_order)
        new_order.user_id = False
        # if delivery_address:
        #     new_order.partner_shipping_id = delivery_address
        if self.note:
            new_order.notes = self.note
        new_order.date_planned = self.commitment_date
        return new_order._convert_to_write(new_order._cache)

    def _prepare_purchase_order_line_data(self, sale_line, dest_company, purchase_order):
        """Generate the Sale Order Line values from the PO line
        :param purchase_line : the origin Purchase Order Line
        :rtype purchase_line : purchase.order.line record
        :param dest_company : the company of the created SO
        :rtype dest_company : res.company record
        :param sale_order : the Sale Order
        """
        new_line = self.env["purchase.order.line"].new(
            {
                "order_id": purchase_order.id,
                "product_id": sale_line.product_id.id,
                "product_uom": sale_line.product_uom.id,
                "product_uom_qty": sale_line.product_uom_qty,
                "product_qty": sale_line.product_uom_qty,
                "auto_sale_line_id": sale_line.id,
                "price_unit": sale_line.price_unit,
                "display_type": sale_line.display_type,
            }
        )
        for onchange_method in new_line._onchange_methods["product_id"]:
            onchange_method(new_line)
        new_line.update({"product_uom": sale_line.product_uom.id, 
                         "product_uom_qty": sale_line.product_uom_qty, 
                         "product_qty": sale_line.product_uom_qty})
        for onchange_method in new_line._onchange_methods["product_qty"]:
            onchange_method(new_line)
        if new_line.display_type in ["line_section", "line_note"]:
            new_line.update({"name": sale_line.name})
        return new_line._convert_to_write(new_line._cache)
