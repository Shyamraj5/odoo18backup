from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MatchMovePayment(models.Model):
    _name = "match.move.payment"
    _description = "Match Move Payment"
    _check_company_auto = True

    payment_id = fields.Many2one("account.payment", string="Payment")
    move_id = fields.Many2one(
        "account.move",
        string="Move",
        check_company=True,
        required=True,
    )
    move_id_domain = fields.Binary(
        string="Move Domain",
        compute="_compute_move_id_domain",
        help="The domain to apply to the move_id field.",
    )
    amount_due = fields.Monetary(
        string="Amount Due",
        compute="_compute_move_values",
        store=True,
    )
    amount_paid = fields.Monetary(
        string="Amount Paid",
        compute="_compute_move_values",
        store=True,
    )
    is_full_payment = fields.Boolean(
        string="Is Full Payment",
        default=False,
    )
    amount = fields.Monetary(string="Amount")
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

    @api.depends("move_id", "move_id")
    def _compute_move_values(self):
        for record in self:
            if record.move_id:
                record.update(
                    {
                        "amount_due": record.move_id.amount_residual,
                        "amount_paid": record.move_id.amount_total
                        - record.move_id.amount_residual,
                    }
                )
            else:
                record.update(
                    {
                        "amount_due": 0.0,
                        "amount_paid": 0.0,
                    }
                )

    @api.onchange("is_full_payment")
    def _onchange_is_full_payment(self):
        if self.is_full_payment:
            self.amount = self.amount_due
        else:
            self.amount = 0.0

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
