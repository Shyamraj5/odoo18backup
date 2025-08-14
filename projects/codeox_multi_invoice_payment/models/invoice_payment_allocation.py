from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class InvoicePaymentAllocation(models.Model):
    _name = "invoice.payment.allocation"
    _description = "Invoice Payment Allocation"
    _check_company_auto = False

    payment_id = fields.Many2one("account.payment", string="Payment")
    move_id = fields.Many2one(
        "account.move",
        string="Move",
        check_company=False,
        required=True,
    )
    move_id_domain = fields.Binary(
        string="Move Domain",
        compute="_compute_move_id_domain",
        help="The domain to apply to the move_id field.",
    )
    amount = fields.Monetary(string="Amount", readonly=False)
    move_amount_due = fields.Monetary(
        string="Due Amount",
        compute="_compute_move_amounts",
        store=True,
    )
    move_amount_paid = fields.Monetary(
        string="Paid Amount",
        compute="_compute_move_amounts",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        compute="_compute_currency_id",
        store=True,
        readonly=False,
        precompute=True,
        help="The payment's currency.",
    )
    date = fields.Date(string="Date")
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="move_id.partner_id",
        store=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="payment_id.company_id",
        store=True,
    )
    mark_fully_paid = fields.Boolean(string="Mark Fully Paid")

    @api.onchange("mark_fully_paid")
    def _onchange_mark_fully_paid(self):
        if self.payment_id.state == "draft" and self.mark_fully_paid:
            self.amount = self.move_amount_due

    @api.depends("move_id", "move_id.amount_paid", "move_id.amount_residual")
    def _compute_move_amounts(self):
        for record in self:
            if record.payment_id.state == "draft":
                record.write(
                    {
                        "move_amount_due": record.move_id.amount_residual,
                        "move_amount_paid": record.move_id.amount_total
                        - record.move_id.amount_residual,
                    }
                )
            else:
                due_amount = record.move_amount_due or 0.0
                paid_amount = record.move_amount_paid or 0.0
                record.write(
                    {
                        "move_amount_due": due_amount,
                        "move_amount_paid": paid_amount,
                    }
                )

    @api.depends("payment_id")
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = record.payment_id.currency_id.id

    @api.constrains("amount")
    def _check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError(_("The amount must be positive."))
            if record.amount > record.payment_id.amount:
                raise ValidationError(
                    _(
                        "The amount must be less than or equal to the payment amount "
                        "for move %s."
                    )
                    % record.move_id.name
                )
            if record.amount > record.move_id.amount_residual:
                raise ValidationError(
                    _(
                        "The amount must be less than or equal to the invoice amount "
                        "for move %s."
                    )
                    % record.move_id.name
                )

    @api.depends("payment_id", "payment_id.payment_type", "payment_id.partner_id")
    def _compute_move_id_domain(self):
        for record in self:
            if record.payment_id.payment_type == "outbound":
                record.move_id_domain = [
                    ("move_type", "in", ("in_invoice", "out_refund")),
                    ("state", "=", "posted"),
                    ("partner_id", "=", record.payment_id.partner_id.id),
                    ("amount_residual", ">", 0.0),
                ]
            else:
                record.move_id_domain = [
                    ("move_type", "in", ("out_invoice", "in_refund")),
                    ("state", "=", "posted"),
                    ("partner_id", "=", record.payment_id.partner_id.id),
                    ("amount_residual", ">", 0.0),
                ]
