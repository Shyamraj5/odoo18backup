from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError
from datetime import timedelta


class PostDatedCheck(models.Model):
    _name = "post.dated.check"
    _inherit = ["mail.thread", "analytic.mixin"]
    _description = "Post Dated Cheque"
    _order = "create_date desc"

    name = fields.Char(
        string="Name",
        required=True,
        default=lambda self: _("New"),
        copy=False,
        tracking=True,
    )
    date = fields.Date(
        string="Date",
        required=True,
        default=fields.Date.today(),
        copy=True,
    )
    ref_no = fields.Char(string="Ref No")
    partner_id = fields.Many2one("res.partner", string="Partner", required=True, index=True, copy=True)
    check_date = fields.Date(
        string="Cheque Date",
        required=True,
        default=fields.Date.today(),
        copy=False,
        index=True,
        tracking=True,
    )
    check_number = fields.Char(
        string="Cheque Number",
        copy=False,
        tracking=True,
    )

    partner_name = fields.Char(
        string="Partner Name",
        copy=True,
    )
    is_temp_partner = fields.Boolean(
        string="Is Temp Partner?",
        default=False,
        copy=True,
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        ondelete="restrict",
        copy=True,
    )
    bank_journal_id = fields.Many2one(
        string="Bank Journal", comodel_name="account.journal", copy=True, domain=[("type", "=", "bank")]
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        ondelete="restrict",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    check_amount = fields.Monetary(
        string="Amount",
        required=True,
        default=0.0,
        currency_field="currency_id",
        copy=True,
        tracking=True,
    )
    amount_total = fields.Monetary(
        string="Total", store=True, readonly=True, compute="_compute_amount_pdc"
    )

    payment_type = fields.Selection(
        [("receive_money", "Receive Money"), ("send_money", "Send Money")],
        string="Payment Type",
        default="receive_money",
    )

    invoice_ids = fields.Many2many("account.move", string="Invoices")
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        index=True,
        default=lambda self: self.env.company.id,
    )
    company_currency_id = fields.Many2one(
        string="Company Currency",
        comodel_name="res.currency",
        ondelete="restrict",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("pending", "Pending"),
            ("authorized", "Authorized"),
            ("approved", "Approved"),
            ("received", "PDC Received"),
            ("submitted", "PDC Submitted"),
            ("deposited", "PDC Deposited"),
            ("bounced", "Bounced"),
            ("cancel", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
        required=True,
        copy=False,
    )
    pdc_type = fields.Selection(
        string="PDC Type",
        selection=[("customer", "Customer"), ("vendor", "Vendor")],
        required=True,
        copy=True,
    )
    submitted_received_move_ids = fields.Many2many(
        relation="pdc_submitted_received_move_rel",
        string="Submitted Received Moves",
        copy=False,
        comodel_name="account.move",
    )
    deposited_move_ids = fields.Many2many(
        relation="pdc_deposited_move_rel",
        string="Deposited Move",
        copy=False,
        comodel_name="account.move",
    )
    bounced_move_ids = fields.Many2many(
        relation="pdc_bounced_move_rel",
        string="Bounced Moves",
        copy=False,
        comodel_name="account.move",
    )
    is_deposited_shown = fields.Boolean(
        string="Is Deposited Shown",
        compute="_compute_is_button_box_shown",
    )
    is_bounced_shown = fields.Boolean(
        string="Is Bounced Shown",
        compute="_compute_is_button_box_shown",
    )
    is_submitted_received_shown = fields.Boolean(
        string="Is Submitted Received Shown",
        compute="_compute_is_button_box_shown",
    )
    account_id = fields.Many2one(
        "account.account", string="Select Account", related="bank_journal_id.default_account_id"
    )
    account_new_id = fields.Many2one("account.account", string="Account", required=True)
    cancel_journal_entry = fields.Many2one("account.move", string="Cancel journal entry")
    memo = fields.Text("Memo")
    payment_line_ids = fields.One2many("post.dated.check.line", "payment_id", "Payment")
    discount_account_id = fields.Many2one('account.account', string="Discount Account", related="company_id.pdc_discount_account_id")
    discount_amount = fields.Monetary(string="Discount Amount", store=True)
    total_discount = fields.Monetary(string="Total Discount", compute = "_compute_total_discount",store=True)

    @api.model_create_multi
    def create(self, vals_list):
        # for vals in vals_list:
        #     if vals.get('check_amount', 0.0) <= 0.0:
        res = super(PostDatedCheck, self).create(vals_list)
        for rec in res:
            if rec.check_amount <= 0.0:
                raise UserError(_("The check amount must be greater than zero."))
            if rec.check_amount <= 0.0:
                raise UserError(_("The check amount must be greater than zero."))
            if any(line.discount_perc > 0 for line in res.payment_line_ids) and rec.discount_amount > 0:
                raise UserError(_("Discount amount and percentage should not be given at the same time"))
        return res

    @api.depends("payment_line_ids.amount","discount_amount")
    def _compute_amount_pdc(self):
        amount_total = 0.0
        for payment in self:
            for line in payment.payment_line_ids:
                amount_total += line.amountpaid
            if payment.discount_amount > 0:
                amount_total -=  payment.discount_amount
            payment.update({
                "amount_total": amount_total,
                "check_amount" : amount_total
                })

    @api.depends("payment_line_ids.discount_amt","discount_amount")
    def _compute_total_discount(self):
        discount_amount = 0.0
        for payment in self:
            # if not payment.pos_session_id:
            if payment.payment_line_ids:
                for line in payment.payment_line_ids:
                    discount_amount += line.discount_amt
                if payment.discount_amount > 0:
                    discount_amount += payment.discount_amount
                payment.update(
                    {
                        "total_discount":discount_amount
                    }
        )

    def _compute_is_button_box_shown(self):
        for record in self:
            record.is_deposited_shown = bool(record.deposited_move_ids)
            record.is_bounced_shown = bool(record.bounced_move_ids)
            record.is_submitted_received_shown = bool(record.submitted_received_move_ids)

    
    prepared_id = fields.Many2one("res.users", string="")
    customer_domain = fields.Char(compute="_compute_customer_domain")

    @api.depends("pdc_type", "partner_id")
    def _compute_customer_domain(self):
        for rec in self:
            if rec.pdc_type == "customer":
                rec.customer_domain = "[('customer_rank', '>', 0)]"
            elif rec.pdc_type == "vendor":
                rec.customer_domain = "[('supplier_rank', '>', 0)]"
            else:
                rec.customer_domain = "[]"

    @api.onchange("pdc_type", "partner_id")
    def _onchange_pdc_type(self):
        if self.pdc_type == "customer":
            if self.partner_id:
                self.account_new_id = self.partner_id.property_account_receivable_id.id
        elif self.pdc_type == "vendor":
            if self.partner_id:
                self.account_new_id = self.partner_id.property_account_payable_id.id

    def action_pdc_send_receive(self):
        discount_amount = 0 
        total_without_discount = 0
        for record in self:
            today = fields.Date.context_today(self)
            year = today.year
            if record.pdc_type == "customer":
                if self.env["ir.sequence"].search([("code", "=", "post.dated.check.customer.sequence")], limit=1):
                    end_code = self.env["ir.sequence"].next_by_code("post.dated.check.customer.sequence")
                    record.name = "PDCR" + "/" + "%s" % (year) + "/" + str(end_code)
                state = "received"
                debit_account_id = self.env.company.pdc_account_receivable_id.id
                credit_account_id = record.account_new_id.id
                journal_id = self.env.company.received_journal_id.id

            else:
                if self.env["ir.sequence"].search([("code", "=", "post.dated.check.vendor.sequence")], limit=1):
                    end_code = self.env["ir.sequence"].next_by_code("post.dated.check.vendor.sequence")
                    record.name = "PDCI" + "/" + "%s" % (year) + "/" + str(end_code)
                state = "submitted"

                debit_account_id = record.account_new_id.id
                credit_account_id = self.env.company.pdc_account_payable_id.id
                journal_id = self.env.company.issued_journal_id.id
                discount_account_id = record.discount_account_id.id
            if not debit_account_id or not credit_account_id:
                raise UserError(_("Please configure the PDC Payable/Receivable Account"))
            if (record.discount_amount > 0 or any(line.discount_perc > 0 for line in self.payment_line_ids)) and not discount_account_id:
                raise UserError(_("Please configure the PDC Discount Account"))
            
            
            for line in self.payment_line_ids:
                discount_percentage = line.discount_perc or 0
                if discount_percentage: 
                    balance_amount = line.amount
                    line_discount_amount = balance_amount * discount_percentage
                    discount_amount += line_discount_amount
                    total_without_discount += line_discount_amount + record.check_amount + record.discount_amount
                if line.is_paid:
                    line.invoice_id.is_paid = True
            

            line_list = []
            label_name = "" if not record.is_temp_partner else record.partner_name
            memo = ""
            check_number = ""
            if self.memo:
                memo = "-" + str(self.memo)
            if record.check_number:
                check_number = record.check_number + "-"

            line_list.append(
                (
                    0,
                    0,
                    {
                        "account_id": debit_account_id,
                        "debit": record.currency_id._convert(record.check_amount, self.env.company.currency_id),
                        "credit": 0,
                        "amount_currency": record.check_amount,
                        "currency_id": record.currency_id.id,
                        "name": check_number + str(record.check_date) + label_name + memo,
                        "analytic_distribution": record.analytic_distribution,
                        "partner_id": record.partner_id.id,
                    },
                )
            )
            line_list.append(
                (
                    0,
                    0,
                    {
                        "account_id": credit_account_id,
                        "amount_currency": ((total_without_discount if total_without_discount > 0 else (record.check_amount + record.discount_amount)) * -1),
                        "debit": 0,
                        "credit": record.currency_id._convert(total_without_discount if total_without_discount > 0 else (record.check_amount + record.discount_amount), self.env.company.currency_id),
                        "currency_id": record.currency_id.id,
                        "name": check_number + str(record.check_date) + label_name + memo,
                        "partner_id": "",
                    },
                )
            )
            total_discount = 0
            if discount_amount > 0 and record.discount_amount > 0:
                total_discount += discount_amount + record.discount_amount
            elif discount_amount > 0 or record.discount_amount > 0:
                total_discount += discount_amount or record.discount_amount

            if total_discount > 0:
                line_list += [
                    Command.create({
                    "account_id": discount_account_id,
                    "amount_currency": (total_discount),
                    "debit": record.currency_id._convert(total_discount, self.env.company.currency_id),
                    "credit": 0,
                    "currency_id": record.currency_id.id,
                    "partner_id": record.partner_id.id,
                    "name": check_number + str(record.check_date) + label_name + memo,
                })
                ]

            values = {
                "date": record.date,
                "move_type": "entry",
                "line_ids": line_list,
                "journal_id": journal_id,
                "partner_id": record.partner_id.id,
                "ref": record.ref_no,
            }
            move_id = self.env["account.move"].create(values)
            move_id.action_post()
            for each in self.payment_line_ids:
                domain = [('account_type', 'in', ('asset_receivable', 'liability_payable')), ('reconciled', '=', False), ('account_id.is_pdc', '=', False)]
                if each.amountpaid > 0:
                    if each.invoice_id:
                        payment_lines = move_id.line_ids.filtered_domain(domain)
                        if payment_lines:
                            for pline in payment_lines:
                                each.invoice_id.js_assign_outstanding_line(pline.id)
                    elif each.move_line_id:                                                
                        to_reconcile = each.move_line_id
                        for payment, lines in zip([move_id], to_reconcile):
                            payment_lines = payment.line_ids.filtered_domain(domain)
                            for account in payment_lines.account_id:
                                (payment_lines + lines).filtered_domain([('account_id', '=', account.id),
                                                                        ('reconciled', '=', False)]).reconcile()
            record.name = move_id.name
            record.submitted_received_move_ids = [(4, move_id.id)]
            record.state = state

    def action_pdc_bounce(self):
        for record in self:
            if record.pdc_type == "customer":
                if self.submitted_received_move_ids:
                    move_ids = self.submitted_received_move_ids
                    move_ids.button_draft()
                    move_ids.button_cancel()
                    record.state = "bounced"

            else:
                if self.submitted_received_move_ids:
                    move_ids = self.submitted_received_move_ids
                    move_ids.button_draft()
                    move_ids.button_cancel()
                    record.state = "bounced"

    def action_pdc_deposit(self, date=False):
        for record in self:
            if not record.bank_journal_id:
                raise UserError(_("Please select the Bank Journal."))
            date = date if date else record.check_date
            if record.pdc_type == "customer":
                debit_account_id = record.account_id.id
                if not debit_account_id:
                    raise UserError(_("Please set a bank account for bank journal."))
                credit_account_id = self.env.company.pdc_account_receivable_id.id
                journal_id = self.env.company.received_journal_id.id
            else:
                debit_account_id = self.env.company.pdc_account_payable_id.id
                credit_account_id = record.account_id.id
                journal_id = self.env.company.issued_journal_id.id
                if not credit_account_id:
                    raise UserError(_("Please set a bank account for bank journal."))
            if not debit_account_id or not credit_account_id:
                raise UserError(_("Please configure the PDC Payable/Receivable Account"))
            line_list = []
            partner_name = record.partner_id.name if not record.is_temp_partner else record.partner_name
            memo = ""
            check_number = ""
            if self.memo:
                memo = "-" + str(self.memo)
            if record.check_number:
                check_number = record.check_number + "-"
            line_list.append(
                (
                    0,
                    0,
                    {
                        "account_id": debit_account_id,
                        "credit": 0,
                        "amount_currency": record.check_amount,
                        "currency_id": record.currency_id.id,
                        "partner_id": record.partner_id.id,
                        "debit": record.currency_id._convert(record.check_amount, self.env.company.currency_id),
                        "name": partner_name + "-" + check_number + str(record.check_date) + memo,
                        "analytic_distribution": record.analytic_distribution,
                    },
                )
            )
            line_list.append(
                (
                    0,
                    0,
                    {
                        "account_id": credit_account_id,
                        "amount_currency": (record.check_amount * -1),
                        "debit": 0,
                        "currency_id": record.currency_id.id,
                        "credit": record.currency_id._convert(record.check_amount, self.env.company.currency_id),
                        "partner_id": record.partner_id.id,
                        "name": partner_name + check_number + str(record.check_date) + memo,
                    },
                )
            )
            if date.today() < date:
                raise UserError(_("You can only deposit the check on or before check date"))
            date.today() if date.today() > date else date
            values = {
                "date": date,
                "move_type": "entry",
                "line_ids": line_list,
                "journal_id": journal_id,
                "ref": record.name,
            }
            move_id = self.env["account.move"].create(values)
            move_id.action_post()
            record.deposited_move_ids = [(4, move_id.id)]
            record.state = "deposited"

    def _prepare_default_reversal_bounce(self, move):
        return {
            "ref": _("Reversal of: %s") % (move.name),
            "date": self.date or move.date,
            "invoice_date": move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
            "journal_id": move.journal_id.id,
            "invoice_payment_term_id": None,
            "auto_post":'no',
            "invoice_user_id": move.invoice_user_id.id,
        }

    def cancel_entry(self):
        moves = self.env["account.move"].browse(self.submitted_received_move_ids.id)
        # Create default values.
        default_values_list = []
        for move in moves:
            default_values_list.append(self._prepare_default_reversal_bounce(move))

        batches = [
            [self.env["account.move"], [], True],  # Moves to be cancelled by the reverses.
            [self.env["account.move"], [], False],  # Others.
        ]
        for move, default_vals in zip(moves, default_values_list):
            is_auto_post = bool(default_vals.get("auto_post"))
            is_cancel_needed = not is_auto_post and self.refund_method in ("cancel", "modify")
            batch_index = 0 if is_cancel_needed else 1
            batches[batch_index][0] |= move
            batches[batch_index][1].append(default_vals)

        # Handle reverse method.
        moves_to_redirect = self.env["account.move"]
        for moves, default_values_list, is_cancel_needed in batches:
            new_moves = moves._reverse_moves(default_values_list, cancel=is_cancel_needed)
            moves_to_redirect |= new_moves
        moves_to_redirect.action_post()
        self.write({"state": "cancel", "cancel_journal_entry": moves_to_redirect.id})

    def action_open_reconcile(self):
        # Open reconciliation view for customers and suppliers
        reconcile_mode = "suppliers"
        if self.env.context.get("default_pdc_type", False) == "customer":
            reconcile_mode = "customers"
        accounts = self.partner_id.property_account_payable_id
        if reconcile_mode == "customers":
            accounts = self.partner_id.property_account_receivable_id
        action_context = {
            "show_mode_selector": True,
            "partner_ids": [self.partner_id.id],
            "mode": reconcile_mode,
            "account_ids": accounts.ids,
        }
        return {
            "type": "ir.actions.client",
            "tag": "manual_reconciliation_view",
            "context": action_context,
        }

    def action_open_submit_receive_moves(self):
        for record in self:
            return {
                "name": _("Submitted Received Moves"),
                "view_mode": "list,form",
                "res_model": "account.move",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", record.submitted_received_move_ids.ids)],
                "context": {"create": False},
            }

    def action_open_bounced_moves(self):
        for record in self:
            return {
                "name": _("Bounced Moves"),
                "view_mode": "list,form",
                "res_model": "account.move",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", record.bounced_move_ids.ids)],
                "context": {"create": False},
            }

    def action_open_deposited_moves(self):
        for record in self:
            return {
                "name": _("Deposited Moves"),
                "view_mode": "list,form",
                "res_model": "account.move",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", record.deposited_move_ids.ids)],
                "context": {"create": False},
            }

    def action_deposit_server_action(self):
        pdc_obj = self.env["post.dated.check"].browse(self._context.get("active_ids"))
        datas = []
        for pdc in pdc_obj:
            if pdc.state in ["received", "submitted"]:
                datas.append(pdc.id)
            else:
                raise UserError(_("Please select submitted or Received PDC Payments"))
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "post.dated.wizard",
            "target": "new",
            "context": {
                "default_pdc_ids": [(6, 0, datas)],
            },
        }

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("You cannot delete a PDC Payment(s) which is not draft state"))
        return super(PostDatedCheck, self).unlink()

    reconciled_moves_ids = fields.Many2many("account.move", compute="_compute_move_ids")
    reconciled_moves_count = fields.Integer("Reconciled moves count", compute="_compute_move_ids")

    def _compute_move_ids(self):
        for rec in self:
            move_ids = []
            for res in rec.submitted_received_move_ids:
                try:
                    partials = res._get_reconciled_invoices_partials()
                    for item in partials:
                        move_ids.append(item[2].move_id.id)
                except Exception:
                    continue
            rec.reconciled_moves_ids = [(6, 0, move_ids)]
            rec.reconciled_moves_count = len(move_ids)

    def open_reconciled_moves(self):
        return {
            "name": "Reconciled Entries",
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "account.move",
            "domain": [("id", "in", self.reconciled_moves_ids.ids)],
            "target": "current",
        }

    def get_reconciled_moves(self):
        move_vals = []
        for rec in self.reconciled_moves_ids:
            move_vals.append(
                {
                    "date": rec.date,
                    "v_no": rec.name,
                    "ref": rec.ref,
                    "amount": rec.total,
                    "paid": rec.paid_amount,
                    "balance": rec.total - rec.paid_amount,
                }
            )

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        self.payment_line_ids = False
        invoices = []
        details = {}
        invoice_ids = []
        invoice = self.env["account.move"].search(
                [
                    ("move_type", "in", ("in_invoice","in_refund","out_invoice","out_refund","out_receipt","in_receipt")),
                    ("partner_id", "=", self.partner_id.id),
                    ("state", "=", "posted"),
                    ("amount_residual", ">", 0),
                    ("is_paid", "=", False),
                ],order="invoice_date desc"
            )
        journal_ids = self.env["account.move.line"].search([
                ("move_id.move_type", "=", "entry"),
                ("move_id.journal_id.code", "=", "MISC"),('reconciled','=',False),
                ("matching_number", "=", False),
                ("partner_id", "=", self.partner_id.id),
                ("account_id.account_type", "in", ("liability_payable", "asset_receivable")),
                ("account_id.is_pdc", "=", False),
                ("parent_state", "=", "posted"),

            ], order="invoice_date desc")

        account_id = False

        if invoice:
            for inv in invoice:  
                account_id = (
                    inv.partner_id.commercial_partner_id.property_account_receivable_id.id
                    if self.payment_type == "receive_money"
                    else inv.partner_id.commercial_partner_id.property_account_payable_id.id
                )
                if inv.move_type == "in_refund":
                    amount_residual = inv.amount_residual * -1
                else:
                    amount_residual = inv.amount_residual
                details = (
                    0,
                    0,
                    {
                        "invoice_id": inv.id,
                        "account_id": account_id if account_id else False,
                        "invoice_no": inv.name,
                        "invoice_date": inv.invoice_date,
                        "invoice_duedate": inv.invoice_date_due,
                        "amount": inv.amount_total,
                        "balance": amount_residual,
                        "amountpaid": 0,
                    },
                )
                invoice_ids.append(inv.id)
                invoices.append(details)

        if journal_ids:
            for move in journal_ids:
                details_1 = (
                            0,
                            0,
                            {
                                "move_line_id" :move.id,
                                "invoice_no": move.move_id.name,
                                "move_ref":move.name,
                                "invoice_date": move.move_id.date,
                                "amount": move.balance,
                            },
                        )
                invoice_ids.append(move.move_id.id)
                invoices.append(details_1)

        self.payment_line_ids = invoices

    def action_done(self):
        for rec in self.payment_line_ids:
            if self.deposited_move_ids:
                if self.payment_type == "receive_money":
                    inv = rec.invoice_id
                    for _invoice in inv:
                        line_id = self.env["account.move.line"].search(
                            [("move_id", "=", self.submitted_received_move_ids.id), ("amount_residual", "<", 0)],
                            limit=1,
                        )

                    for each_invoice in _invoice:
                        if line_id.amount_residual < 0:
                            each_invoice.js_assign_outstanding_line(line_id.id)
                if self.payment_type == "send_money":
                    inv = rec.invoice_id
                    for _invoice in inv:
                        line_id = self.env["account.move.line"].search(
                            [("move_id", "=", self.submitted_received_move_ids.id), ("amount_residual", ">", 0)],
                            limit=1,
                        )

                    for each_invoice in _invoice:
                        if line_id.amount_residual > 0:
                            each_invoice.js_assign_outstanding_line(line_id.id)
            else:
                raise UserError(_("Please Deposit Amount To Reconcile"))

    #APPROVAL CUSTOMISATION

    is_all_approved = fields.Boolean(compute="_compute_is_all_approved", default=False)
    
    @api.model
    def _get_team_id(self):
        approval_team_id = False
        payment_team = self.env["payment.team"].search([('company_id', '=', self.env.company.id)], limit=1)
        if payment_team:
            approval_team_id = payment_team.id
        return approval_team_id
    payment_approval = fields.Many2one('payment.team', check_company=True, string='Payment Approval',default=_get_team_id)

    approval_route_ids = fields.One2many(
        'post.dated.check.approval', 'check_id', string='Approval Route'
    )
    is_send_receive_visible = fields.Boolean(
        compute="_compute_is_send_receive_visible",
        string="Send/Receive Button visible",
    )
    reason_for_reject = fields.Text(string="Reason for Reject")


    @api.depends('state')
    def _compute_is_send_receive_visible(self):
        for record in self:
            record.is_send_receive_visible = (record.state == 'approved')


    @api.model_create_multi
    def create(self, vals):
        record = super(PostDatedCheck, self).create(vals)
        record.state = 'to_approve'
        record._create_approval_lines()
        return record

    @api.depends()
    def _compute_is_all_approved(self):
        for record in self:
            record.is_all_approved = all(line.state == 'approved' for line in record.approval_route_ids)

    def _create_approval_lines(self):
        if self.payment_approval:
            new_approval_lines = []
            first_line = True
            for approver in self.payment_approval.approver_ids:
                for user in approver.user_ids:
                    new_approval_lines.append((0, 0, {
                        'user_id': user.id,
                        'state': 'pending' if first_line else 'to_approve'
                    }))
                    first_line = False
            self.approval_route_ids = new_approval_lines

    def action_approve_line(self):
        next_line = self.approval_route_ids.filtered(lambda line: line.state not in ['approved', 'rejected'])[:1]
        if next_line:
            if not self._can_user_approve(next_line.user_id):
                raise UserError("You do not have permission to approve this document.")
            next_line.state = 'approved'
            approved_lines = self.approval_route_ids.filtered(lambda line: line.state == 'approved')
            if len(approved_lines) == len(self.approval_route_ids):
                self.state = 'approved'
        else:
            raise UserError("No approval lines available to approve.")

    def action_reject_line(self):
        for record in self:
            next_line = record.approval_route_ids.filtered(lambda line: line.state not in ['approved', 'rejected'])[:1]
            if next_line:
                if not record._can_user_approve(next_line.user_id):
                    raise UserError("You do not have permission to reject this document.")
            if not record.reason_for_reject:
                raise UserError("Please provide a reason for rejection before Rejecting.")
            record.state = 'draft'


    def _can_user_approve(self, user_id):

        current_user_ids = self.env.user.ids
        return user_id.id in current_user_ids


class PostDatedCheckApproval(models.Model):
    _name = 'post.dated.check.approval'
    _description = 'Post Dated Check Approval Route'

    check_id = fields.Many2one('post.dated.check', string='Post Dated Check', ondelete='cascade')
    role_id = fields.Many2one('hr.job', string='Role/Position')
    state = fields.Selection([
        ('to_approve', 'To Approve'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    ], string='State', default='to_approve',required=True,store=True)
    user_id = fields.Many2one('res.users', string='Users')

    def _can_user_approve(self):
        current_user_jobs = [self.env.user.employee_id.job_id.id] + self.env.user.employee_id.job_ids.ids
        return self.role_id.id in current_user_jobs


class PostDatedCheckLine(models.Model):
    _name = "post.dated.check.line"
    _description = "Post Dated Cheque Line"

    is_paid = fields.Boolean(string="Paid")
    payment_id = fields.Many2one("post.dated.check", "Payment Lines")
    invoice_id = fields.Many2one("account.move", "Invoice")
    move_line_id = fields.Many2one("account.move.line", "Account Move Line")
    move_ref = fields.Char(string="Bill Reference", related='invoice_id.ref', store=True)
    account_id = fields.Many2one("account.account", "Account")
    invoice_no = fields.Char("Invoice Number")
    vendor_reference = fields.Char("Vendor Reference", related="invoice_id.ref")
    invoice_date = fields.Date("Invoice Date")
    invoice_duedate = fields.Date("Due Date")
    amount = fields.Float("Amount")
    discount_perc = fields.Float("Discount %")
    discount_amt = fields.Float(string="Discount Amt")
    balance = fields.Float("Balance")
    full_reconcile = fields.Boolean(string="Full Reconcile", store=False)
    amountpaid = fields.Float("Amount to be Paid")
    account_payment_id = fields.Many2one("account.payment", "Payment Reference")
    deduction_amount = fields.Float(string='Deduction Amount', compute='_compute_deduction_amount')

    @api.depends('invoice_id')
    def _compute_deduction_amount(self):
        for line in self:
            line.deduction_amount = 0.0
            bill = line.invoice_id
            refunds = self.env['account.move'].search([
                ('move_type', '=', 'in_refund'),
                ('reversed_entry_id', '=', bill.id),
                ('state', '=', 'posted')
            ])
            if refunds:
                line.deduction_amount = bill.amount_total

    @api.onchange("full_reconcile","account_payment_id")
    def _onchange_full_reconcile(self):
        for payment in self:
            if payment.full_reconcile:
                payment.is_paid = True
                if payment.discount_perc:
                    disc_amount = payment.amount * payment.discount_perc
                    payment.amountpaid = payment.amount - disc_amount
                    payment.discount_amt = disc_amount
                    if payment.discount_amt < 0:
                        payment.discount_amt = disc_amount * -1
                    if payment.amountpaid < 0:
                        payment.amountpaid = payment.amountpaid * -1
                elif payment.amount < 0 and not payment.move_line_id:
                    payment.amountpaid = payment.amount * -1
                else:
                    payment.amountpaid = payment.amount
                if payment.invoice_id.move_type == 'in_refund':
                    payment.amountpaid = payment.amount * -1
                if (payment.move_line_id.debit > 0 or payment.move_line_id.credit > 0) and payment.move_line_id:
                    payment.amountpaid = payment.amount * -1
            else:
                payment.amountpaid = 0.0
                payment.discount_amt = 0.0
            # if payment.account_payment_id:
            #     discount_amount = self.account_payment_id.discount_amount
            #     if discount_amount > 0:
            #         payment.discount_perc = 0
            #         payment.amountpaid = payment.amount
            if payment.full_reconcile and payment.amountpaid != 0.0:
                payment.is_paid = True
            else:
                payment.is_paid = False

    # @api.onchange("discount_perc")
    # def onchange_discount_percentage(self):
    #     if self.discount_perc:
    #         self.account_payment_id.discount_amount = 0
