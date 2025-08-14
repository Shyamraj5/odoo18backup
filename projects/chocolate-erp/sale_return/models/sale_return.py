from odoo import models, fields, api, _
from odoo.exceptions import UserError
from markupsafe import Markup


class SaleReturn(models.Model):
    _name = "sale.return"
    _description = "Sale Return"
    _inherit = "mail.thread"

    name = fields.Char("Name", copy=False, default="New")
    draft_sequence = fields.Char("Draft Sequence", copy=False, default="New")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting", "Waiting Approval"),
            ("approved", "Approved"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        copy=False,
        default="draft",
    )
    date = fields.Date("Date", copy=False, default=fields.Date.today())
    confirmation_force_date = fields.Datetime(string='Confirm Force Date', index=True, help="Date on which the sales order is confirmed.", copy=False)
    partner_id = fields.Many2one("res.partner", string="Customer")
    sale_order_id = fields.Many2one("sale.order", string="Sale Order")
    return_line_ids = fields.One2many("sale.return.line", "return_id", string="Return Lines", copy=False)
    user_id = fields.Many2one("res.users", string="Salesperson", default=lambda self: self.env.user.id)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company.id)
    picking_ids = fields.One2many("stock.picking", "sale_return_id", string="Return Stock Receipts")
    picking_count = fields.Integer("Return Receipt Count", compute="_compute_return_receipt_count")
    credit_note_ids = fields.One2many("account.move", "sale_return_id", string="Credit Notes")
    credit_note_count = fields.Integer("Credit Note Count", compute="_compute_credit_note_count")
    show_credit_note_button = fields.Boolean("Show Credit Note", compute="_compute_show_credit_note_button")
    display_name = fields.Char(compute="_compute_display_name", string="Name")
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    taxable_totals = fields.Monetary("Taxable Amount", compute="_compute_taxable_amount")
    discount_totals = fields.Monetary("Discount Amount", compute="_compute_discount_totals")
    grand_totals = fields.Monetary("Grand Total", compute="_compute_grand_totals")
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)


    def action_open_round_off_wizard(self):
        """Open the round-off wizard for sale return"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Round Off',
            'res_model': 'sale.return.roundoff.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def _compute_taxable_amount(self):
        for rec in self:
            rec.taxable_totals = sum(line.price_subtotal for line in rec.return_line_ids)
    
    def _compute_discount_totals(self):
        for rec in self:
            rec.discount_totals = sum(line.discount_amount for line in rec.return_line_ids)
    
    def _compute_grand_totals(self):
        for rec in self:
            rec.grand_totals = sum(line.total_amount for line in rec.return_line_ids)

    @api.depends('return_line_ids.price_subtotal', 'currency_id', 'company_id', 'discount_totals')
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']
        for s_return in self:
            order_lines = s_return.return_line_ids.filtered(lambda x: not x.is_roundoff)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, s_return.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, s_return.company_id)
            s_return.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=s_return.currency_id or s_return.company_id.currency_id,
                company=s_return.company_id,
            )
            if s_return.discount_totals > 0:
                s_return.tax_totals['discount'] = s_return.discount_totals
            round_off = sum(s_return.return_line_ids.filtered(lambda x: x.is_roundoff == True).mapped('price_subtotal'))
            if round_off:
                s_return.tax_totals['round_off'] = round_off
            s_return.tax_totals['total_amount_currency'] = s_return.tax_totals['total_amount_currency'] + round_off
            if 'subtotals' in s_return.tax_totals:
                for subtotal in s_return.tax_totals['subtotals']:
                    if subtotal.get('name') == 'Untaxed Amount':
                        subtotal['name'] = 'Taxable'

    def _compute_return_receipt_count(self):
        for rec in self:
            if rec.picking_ids:
                rec.picking_count = len(rec.picking_ids)
            else:
                rec.picking_count = 0

    def view_pickings(self):
        if len(self.picking_ids) > 1:
            return {
                "name": _("Return Receipts"),
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "domain": [("id", "in", self.picking_ids.ids)],
                "target": "current",
                "view_mode": "list,form",
            }
        else:
            return {
                "name": _("Return Receipt"),
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "res_id": self.picking_ids[0].id,
                "target": "current",
                "view_mode": "form",
            }

    def _compute_credit_note_count(self):
        for rec in self:
            if rec.credit_note_ids:
                rec.credit_note_count = len(rec.credit_note_ids)
            else:
                rec.credit_note_count = 0

    def view_credit_notes(self):
        if len(self.credit_note_ids) > 1:
            return {
                "name": _("Credit Notes"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "domain": [("id", "in", self.credit_note_ids.ids)],
                "target": "current",
                "view_mode": "list,form",
            }
        else:
            return {
                "name": _("Credit Note"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": self.credit_note_ids[0].id,
                "target": "current",
                "view_mode": "form",
            }

    def _compute_show_credit_note_button(self):
        for rec in self:
            if any(line.received_qty > 0 and line.received_qty != line.credit_note_qty for line in rec.return_line_ids):
                rec.show_credit_note_button = True
            else:
                rec.show_credit_note_button = False

    @api.onchange("sale_order_id")
    def _onchange_sale_order_id(self):
        for rec in self:
            if rec.sale_order_id:
                rec.partner_id = rec.sale_order_id.partner_id

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            domain = []
            if rec.partner_id:
                domain.append(("partner_id", "=", rec.partner_id.id))
        return {"domain": {"sale_order_id": domain}}

    @api.model
    def create(self, vals):
        vals["draft_sequence"] = self.env["ir.sequence"].next_by_code("sale.return.draft.seq") or "New"
        if vals.get("sale_order_id"):
            sale_order = self.env["sale.order"].browse(vals.get("sale_order_id"))
            if sale_order.state != "sale":
                raise UserError(_("Return can be created only for confirmed sale order."))
            if sale_order.invoice_status != "invoiced":
                raise UserError(_("Return can be created only for invoiced sale order."))
            if sale_order.state == "sale" and sale_order.invoice_status == "invoiced":
                vals["partner_id"] = sale_order.partner_id.id 
        res = super(SaleReturn, self).create(vals)
        self.env['sale.return.line'].create_return_lines(res)
        return res


    def request_approval(self):
        for rec in self:
            if not rec.return_line_ids:
                self.env['sale.return.line'].create_return_lines(rec)
            for returns in rec.sale_order_id.sale_return_ids:
                stock_picking =rec.env['stock.picking'].search([('sale_return_id','=',returns.id),('state','!=','done')])
                if stock_picking:
                    raise UserError(_(f"Validate receipts of {stock_picking.sale_return_id.name}."))
            for line in rec.return_line_ids.filtered(lambda x: not x.is_roundoff):
                if line.product_id.tracking == "serial":
                    if line.quantity < len(line.lot_ids):
                        raise UserError(
                            _(f"You can enter only {line.quantity} serial numbers for {line.product_id.name}.")
                        )
                    elif line.quantity > len(line.lot_ids):
                        raise UserError(_(f"Enter serial number for all {line.quantity} {line.product_id.name}."))
                elif line.product_id.tracking == "lot":
                    total_lot_capacity = sum(
                        self.env["stock.quant"]
                        .search(
                            [
                                ("lot_id", "in", line.lot_ids.ids),
                                ("location_id.usage", "=", "customer"),
                                ("available_quantity", ">", 0),
                            ]
                        )
                        .mapped("available_quantity")
                    )
                    if line.quantity > total_lot_capacity:
                        raise UserError(
                            _(
                                f"Return quantity {line.quantity} for {line.product_id.name} \
is greater than the available quantity in given lots."
                            )
                        )
                total_return_qty = sum(
                    self.env["sale.return.line"]
                    .search(
                        [
                            ("return_id.sale_order_id", "=", self.sale_order_id.id),
                            ("return_id.state", "not in", ["done", "cancel"]),
                            ("product_id", "=", line.product_id.id),
                        ]
                    )
                    .mapped("quantity")
                )
                total_sale_qty = sum(
                    line.sale_order_line_id.order_id.order_line.filtered(
                        lambda so_line: so_line.product_id == line.product_id
                    ).mapped("qty_delivered")
                )
                if total_return_qty > total_sale_qty:
                    raise UserError(
                        _(
                            f"Total returns created for {line.product_id.name} \
cannot be greater than total delivered by sale."
                        )
                    )
                if line.quantity == 0:
                    raise UserError(_("Return is not possible with zero quantity"))
                if line.quantity > line.sale_order_line_id.qty_delivered:
                    message = f"Return quantity cannot be greater than delivered quantity.\
\nPRODUCT\t\t: {line.product_id.name}\nRETURN QTY\t: {line.quantity} {line.uom_id.name}\
\nDELIVERED QTY\t: {line.sale_order_line_id.qty_delivered} {line.sale_order_line_id.product_uom.name}\n"
                    raise UserError(_(message))
            sales_manager_group_id = self.env.ref("sales_team.group_sale_manager")
            for user in sales_manager_group_id.users:
                notification_ids = []
                notification_ids.append(
                    (
                        0,
                        0,
                        {
                            "res_partner_id": user.partner_id.id,
                            # 'mail_message_id': post.id
                            # "notification_type": "inbox",
                        },
                    )
                )
                post = rec.message_post(
                    body= Markup(
                        "Sales Return <a href=# data-oe-model=%s data-oe-id=%d>%s</a>: Waiting %s for Approval"
                        % (rec._name, rec.id, rec.draft_sequence, user.name)
                    ),
                    message_type="notification",
                    subtype_xmlid="mail.mt_comment"
                    # notification_ids=notification_ids,
                )
                if post:
                    post.write({'notification_ids': notification_ids})

            rec.state = "waiting"

    def approve(self):
        for rec in self:
            for returns in rec.sale_order_id.sale_return_ids:
                stock_picking =rec.env['stock.picking'].search([('sale_return_id','=',returns.id),('state','!=','done')])
                if stock_picking:
                    raise UserError(_(f"Validate receipts of {stock_picking.sale_return_id.name}."))
                if returns.id != rec.id:
                    returns_records =rec.search([('id','=',returns.id),('state','=','approved')])
                    if returns_records:
                        raise UserError(_("Confirm the approved sale returns."))
            message_ids = self.env["mail.message"].search(
                [
                    ("model", "=", "sale.return"),
                    ("res_id", "=", rec.id),
                ]
            )
            chatter_list = []
            for message_id in message_ids:
                original_message = message_id.body.unescape().replace("<span>", "")
                original_message = original_message.replace("</span>", "")
                if original_message[-12:] == "for Approval":
                    chatter_list.append(message_id.id)
            if chatter_list:
                self.env.cr.execute("DELETE FROM mail_message WHERE id in %s", (tuple(chatter_list),))
            rec.message_post(body=_(f"Sales Return {rec.draft_sequence} approved by {self.env.user.name}."))
            rec.state = "approved"

    def reject(self):
        for rec in self:
            message_ids = self.env["mail.message"].search(
                [
                    ("model", "=", "sale.return"),
                    ("res_id", "=", rec.id),
                ]
            )
            chatter_list = []
            for message_id in message_ids:
                original_message = message_id.body.unescape().replace("<span>", "")
                original_message = original_message.replace("</span>", "")
                if original_message[-12:] == "for Approval":
                    chatter_list.append(message_id.id)
            if chatter_list:
                self.env.cr.execute("DELETE FROM mail_message WHERE id in %s", (tuple(chatter_list),))
            rec.message_post(body=_(f"Sales Return {rec.draft_sequence} rejected by {self.env.user.name}."))
            rec.cancel()

    def _prepare_picking_vals(self, picking_type_id, location_id, location_dest_id):
        picking_vals = {
            "picking_type_id": picking_type_id.id,
            "partner_id": self.partner_id.id,
            "origin": f"Return {self.name} for Order {self.sale_order_id.name}",
            "location_dest_id": location_id.id,
            "location_id": location_dest_id.id,
            "move_type": "direct",
            "sale_return_id": self.id,
            "is_return": True,
            # "transfer_date": self.confirmation_force_date,
        }
        return picking_vals

    def confirm(self):
        for rec in self:
            for returns in rec.sale_order_id.sale_return_ids:
                if returns.id != rec.id:
                    stock_picking =rec.env['stock.picking'].search([('sale_return_id','=',returns.id),('state','!=','done')])
                    if stock_picking:
                        raise UserError(_(f"Validate receipts of {stock_picking.sale_return_id.name}."))
            if not rec.sale_order_id or not rec.sale_order_id.picking_ids:
                raise UserError(_("Return can be done only if some delivery has been made for linked sale order."))
            for picking in rec.sale_order_id.picking_ids.filtered(lambda x: x.picking_type_id.code == 'outgoing'):
                return_lines = []
                for line in rec.return_line_ids.filtered(lambda rline: rline.quantity > 0 and not rline.is_roundoff):
                    return_lines.append({
                        "product_id": line.product_id.id,
                        "quantity": line.quantity,
                        "uom_id": line.uom_id.id,
                        "to_refund": True,
                        "move_id": line.sale_order_line_id.move_ids.filtered(lambda x: not x.origin_returned_move_id and x.location_dest_id == picking.location_dest_id).id
                    })
                return_picking_wizard = self.env['stock.return.picking'].create(
                    {
                        'picking_id': picking.id,
                        'product_return_moves': [(0, 0, line) for line in return_lines]
                    }
                )
                new_picking = return_picking_wizard.action_create_returns()
                return_picking = self.env['stock.picking'].browse([new_picking.get('res_id')])
                return_picking.write({
                    "sale_return_id": rec.id,
                    "origin": f"Return {rec.name} for Order {rec.sale_order_id.name}",
                    "is_return": True,
                })
                return_picking.button_validate()
                next_transfers = return_picking._get_next_transfers()
                for next_transfer in next_transfers:
                    next_transfer.button_validate()
                for move in return_picking.move_ids:
                    return_line = rec.return_line_ids.filtered(lambda x: x.sale_order_line_id == move.sale_line_id)
                    move.write({"sale_return_line_id": return_line.id})
            rec.state = "done"

    def _prepare_credit_note_vals(self):
        lines = []
        total_credit_qty = sum((line.received_qty - line.credit_note_qty) for line in self.return_line_ids)
        if total_credit_qty <= 0:
            raise UserError(_("No quantities to create credit note."))
        journal_id = self.env["account.journal"].search(
            [("type", "=", "sale")], limit=1
        )
        for line in self.return_line_ids:
            to_credit_qty = line.received_qty - line.credit_note_qty
            so_line = self.env["sale.order.line"].search(
                [("order_id", "=", line.return_id.sale_order_id.id), ("product_id", "=", line.product_id.id)], limit=1
            )
            line_vals = {
                "display_type": "product",
                "product_id": line.product_id.id,
                "quantity": to_credit_qty if not line.is_roundoff else 1,
                "product_uom_id": line.uom_id.id,
                "account_id": journal_id.default_account_id.id,
                "price_unit": so_line.price_unit or line.unit_price,
                "discount": so_line.discount,
                "tax_ids": [(4, tax) for tax in so_line.tax_id.ids],
                "sale_return_line_id": line.id,
                "sale_line_ids": so_line.ids,
                "is_refund": True,
                "discount_fixed": so_line.discount_fixed,
                "is_roundoff": line.is_roundoff
            }
            lines.append((0, 0, line_vals))
        vals = {
            "move_type": "out_refund",
            "sale_return_id": self.id,
            "partner_id": self.partner_id.id,
            "invoice_line_ids": lines,
            "narration": f"Credit Note for Sale Return:{self.name}",
            "invoice_date": self.confirmation_force_date,
        }
        return vals

    def create_credit_note(self):
        vals = self._prepare_credit_note_vals()
        credit_note_id = self.env["account.move"].create(vals)
        return {
            "name": _("Credit Note"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": credit_note_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def cancel(self):
        for rec in self:
            for picking in rec.picking_ids:
                picking.action_cancel()
            for credit_note in rec.credit_note_ids:
                credit_note.button_cancel()
            rec.state = "cancel"

    def set_to_draft(self):
        for rec in self:
            rec.state = "draft"

    @api.depends("name", "state", "draft_sequence")
    def name_get(self):
        result = []
        for rec in self:
            if rec.state in ["done", "cancel"] and rec.name != "New":
                name = rec.name
            else:
                name = rec.draft_sequence
            result.append((rec.id, name))
        return result

    @api.depends("name", "state", "draft_sequence")
    def _compute_display_name(self):
        for rec in self:
            if rec.state in ["done", "cancel"] and rec.name != "New":
                rec.display_name = rec.name
            else:
                rec.display_name = rec.draft_sequence

    def unlink(self):
        picking_ids = self.picking_ids.filtered(lambda picking: picking.state != "cancel")
        credit_note_ids = self.credit_note_ids.filtered(lambda debit_note: debit_note.state != "cancel")
        if picking_ids or credit_note_ids:
            raise UserError(
                _("Sale return cannot be deleted as there exist related sale orders / receipt / credit note.")
            )
        return super(SaleReturn, self).unlink()


class SaleReturnLine(models.Model):
    _name = "sale.return.line"
    _description = "Sale Return Line"

    return_id = fields.Many2one("sale.return", string="Return")
    product_id = fields.Many2one("product.product", string="Product")
    tracking = fields.Selection(string="Tracking", related="product_id.tracking")
    available_lot_ids = fields.Many2many(
        "stock.lot", "sale_return_available_lots_rel", "sale_return_id", "sale_return_avail_lot_id", string="Available Lots"
    )
    lot_ids = fields.Many2many("stock.lot", "sale_return_lots_rel", "sale_return_id", "sale_return_lot_id", string="Serial Numbers")
    name = fields.Char("Name")
    quantity = fields.Float("Quantity")
    uom_id = fields.Many2one("uom.uom", string="UoM")
    sale_order_line_id = fields.Many2one("sale.order.line", string="Sale Order Line")
    received_qty = fields.Float("Received Qty", compute="_compute_received_qty")
    credit_note_qty = fields.Float("Credit Note Qty", compute="_compute_credit_note_qty")
    product_code = fields.Char("Product Code", related="product_id.default_code")
    lot_id = fields.Many2one("stock.lot", string="Lot", compute="_compute_lot_id") 
    unit_price = fields.Float("Unit Price", compute='_compute_unit_price', store=True)
    discount_percentage = fields.Float("Discount (%)", related="sale_order_line_id.discount")
    discount_amount = fields.Float("Discount Amount", compute="_compute_discount_amount", store=True)
    price_subtotal = fields.Float("Gross Total", compute="_compute_amount", store=True)
    tax_id = fields.Many2many("account.tax", string="Taxes", related="sale_order_line_id.tax_id")
    tax_amount = fields.Float("Tax", compute="_compute_amount", store=True)
    total_amount = fields.Float("Total Amount", compute="_compute_amount", store=True)
    discount_fixed = fields.Float("Discount (Fixed)")
    is_roundoff = fields.Boolean(default=False)

    @api.depends("sale_order_line_id")
    def _compute_lot_id(self):
        for record in self:
            record.lot_id = record.sale_order_line_id.lot_id if record.sale_order_line_id else False

    @api.depends('sale_order_line_id')
    def _compute_unit_price(self):
        for record in self:
            if record.sale_order_line_id:
                record.unit_price = record.sale_order_line_id.price_unit

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **{
                'tax_ids': self.tax_id,
                'quantity': self.quantity,
                'partner_id': self.return_id.sale_order_id.partner_id,
                'currency_id': self.return_id.sale_order_id.currency_id or self.return_id.sale_order_id.company_id.currency_id,
                'rate': self.return_id.sale_order_id.currency_rate,
                'price_unit': self.unit_price,
                'discount': self.discount_percentage,
                **kwargs,
            },
        )

    @api.depends('quantity', 'discount_percentage', 'unit_price', 'tax_id')
    def _compute_amount(self):
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            is_fixed_discount = False
            if line.discount_fixed > 0:
                base_line['discount'] = line.discount_fixed
                is_fixed_discount = True
            self.env['account.tax'].with_context(is_fixed_discount=is_fixed_discount)._add_tax_details_in_base_line(base_line, line.sale_order_line_id.company_id)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.total_amount = base_line['tax_details']['raw_total_included_currency']
            line.tax_amount = line.total_amount - line.price_subtotal
    
    @api.depends('quantity', 'unit_price', 'price_subtotal')
    def _compute_discount_amount(self):
        for line in self.filtered(lambda x: not x.is_roundoff):
            line.discount_amount = (line.quantity * line.unit_price) - line.price_subtotal

    def create_return_lines(self, returns):
        delivered_lines = returns.sale_order_id.order_line.filtered(lambda oline: oline.qty_delivered > 0)
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
                            [("lot_id", "=", lot.id), ("quantity", ">", 0), ("location_id.usage", "=", "customer")]
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
                'lot_ids': available_lot_ids,
                'discount_percentage': order_line.discount,
                'discount_fixed': order_line.discount_fixed
            }
            returns.return_line_ids = [(0, 0, return_line)]

    def _compute_received_qty(self):
        for line in self:
            received_qty = 0
            stock_move_ids = self.env["stock.move"].search(
                [("sale_return_line_id", "=", line.id), ("picking_id.sale_return_id", "=", line.return_id.id)]
            )
            for stock_move in stock_move_ids:
                received_qty += stock_move.quantity
            line.received_qty = received_qty

    def _compute_credit_note_qty(self):
        for line in self:
            credit_note_qty = 0
            account_move_line_ids = self.env["account.move.line"].search(
                [
                    ("sale_return_line_id", "=", line.id),
                    ("move_id.sale_return_id", "=", line.return_id.id),
                    ("move_id.move_type", "=", "out_refund"),
                    ("move_id.state", "!=", "cancel"),
                ]
            )
            for move_line in account_move_line_ids:
                credit_note_qty += move_line.quantity
            line.credit_note_qty = credit_note_qty

    @api.onchange("quantity")
    def _onchange_quantity(self):
        for line in self:
            if line.quantity > line.sale_order_line_id.qty_delivered:
                message = f"Return quantity cannot be greater than delivered quantity.\
\nPRODUCT\t\t: {line.product_id.name}\nRETURN QTY\t: {line.quantity} {line.uom_id.name}\
\nDELIVERED QTY\t: {line.sale_order_line_id.qty_delivered} {line.sale_order_line_id.product_uom.name}\n"
                raise UserError(_(message))
