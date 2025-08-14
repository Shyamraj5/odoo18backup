from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    invoice_payment_allocation_ids = fields.One2many(
        comodel_name="invoice.payment.allocation",
        inverse_name="payment_id",
        string="Invoice Payment Allocations",
    )
    assigned_payment_amount = fields.Float(
        compute="_compute_assigned_payment_amount",
        string="Assigned Payment Amount",
        store=True,
        readonly=True,
    )
    difference_payment_amount = fields.Float(
        compute="_compute_assigned_payment_amount",
        string="Difference Payment Amount",
        store=True,
        readonly=True,
    )
    need_auto_allocation = fields.Boolean(
        string="Need Auto Allocation",
        default=True
    )
    credit = fields.Monetary(related='partner_id.credit', string="Total Receivable", readonly=True, store=True)
    debit = fields.Monetary(related='partner_id.debit', string="Total Payable", readonly=True, store=True)
    
    @api.depends(
        "invoice_payment_allocation_ids",
        "invoice_payment_allocation_ids.amount",
    )
    def _compute_assigned_payment_amount(self):
        for payment in self:
            payment.assigned_payment_amount = sum(
                payment.invoice_payment_allocation_ids.mapped("amount")
            )
            payment.difference_payment_amount = (
                payment.amount - payment.assigned_payment_amount
            )

    @api.onchange("payment_type", "partner_id")
    def _onchange_partner_payment_type(self):
        if self.state == "draft":
            self.invoice_payment_allocation_ids = False
        if self.partner_id:
            # find open invoices/bills for the partner
            if self.payment_type == "outbound":
                move_ids = (
                    self.env["account.move"]
                    .sudo()
                    .search(
                        [
                            ("state", "=", "posted"),
                            ("partner_id", "=", self.partner_id.id),
                            ("amount_residual", ">", 0.0),
                            ("move_type", "in", ("out_refund", "in_invoice")),
                        ],
                        order="invoice_date desc" 
                    )
                )
            else:
                move_ids = (
                    self.env["account.move"]
                    .sudo()
                    .search(
                        [
                            ("state", "=", "posted"),
                            ("partner_id", "=", self.partner_id.id),
                            ("amount_residual", ">", 0.0),
                            ("move_type", "in", ("out_invoice", "in_refund")),
                        ]
                    )
                    
                )
            if move_ids:
                sorted_moves = move_ids.sorted(lambda m: m.name)
                lines_to_add = []
                for move in sorted_moves:
                    lines_to_add.append((0, 0, {"move_id": move.id}))
                self.invoice_payment_allocation_ids = lines_to_add

    def action_post(self):
        res = super().action_post()
        for payment in self.filtered(lambda x: x.invoice_payment_allocation_ids):
            zero_amount_lines = payment.invoice_payment_allocation_ids.filtered(
                lambda line: line.amount <= 0
            )
            zero_amount_lines.unlink()
            payment_line = payment.move_id.line_ids.filtered(
                lambda line: line.account_type
                in ("asset_receivable", "liability_payable")
            )
            for line in payment.invoice_payment_allocation_ids.exists():
                line.move_id.with_context(
                    paid_amount=line.amount
                ).js_assign_outstanding_line(payment_line.id)
        return res


    @api.onchange("amount", "invoice_payment_allocation_ids")
    def _onchange_distribute_payment(self):
        if not self.amount:
            return
        if not self.need_auto_allocation:
            return
        remaining_amount = self.amount
        for line in self.invoice_payment_allocation_ids:
            if remaining_amount > 0:
                # The amount to allocate to the current line
                allocation_amount = min(remaining_amount, line.move_id.amount_residual)
                line.amount = allocation_amount
                # Deduct the allocated amount from the remaining amount
                remaining_amount -= allocation_amount
            else:
                # If no remaining amount, ensure the line amount is zero
                line.amount = 0

        if remaining_amount > 0:
            # If there's leftover amount, notify the user
            raise ValidationError(_(
                "The payment amount exceeds the total residual of the selected invoices. "
                "The remaining amount is %.2f." % remaining_amount
            ))
