# -- coding: utf-8 --
###################################################################################

# Author       :  Zinfog Codelabs Pvt Ltd
# Copyright(c) :  2023-Present Zinfog Codelabs Pvt Ltd (<https://www.zinfog.com>).
# License      :  LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# This program is free software:
# you can modify it under the terms of the GNU Lesser General Public License (LGPL) as
# published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
############################################################

from odoo import models, fields,api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_line_ids = fields.One2many('account.payment.lines', 'account_payment_id')
    remaining_amount = fields.Float(compute='_compute_remaining_amount')

    @api.depends('amount', 'payment_line_ids')
    def _compute_remaining_amount(self):
        for rec in self:
            amt = 0
            if rec.payment_line_ids:
                for line in rec.payment_line_ids:
                    amt += line.amount
                rec.remaining_amount = rec.amount - amt
            else:
                rec.remaining_amount = rec.amount

    @api.onchange('payment_type', 'partner_id')
    def onchange_payment_type(self):
        related_lines_vals = []

        if self.payment_type == 'inbound':
            invoices = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ])

            for invoice in invoices:
                related_lines_vals.append({
                    'account_payment_id': self.id,
                    'move_id': invoice.id,
                    'amount_total': invoice.amount_residual,
                    'amount': invoice.amount_residual,
                    'state': invoice.state,
                    'status': invoice.payment_state,
                })

        elif self.payment_type == 'outbound':  #
            bills = self.env['account.move'].search([
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial'])
            ])

            for bill in bills:
                related_lines_vals.append({
                    'account_payment_id': self.id,
                    'move_id': bill.id,
                    'amount_total': bill.amount_residual,
                    'amount': bill.amount_residual,
                    'state': bill.state,
                    'status': bill.payment_state,
                })

        if self.payment_line_ids:
            self.payment_line_ids = [(5, 0, 0)]  # Clear existing lines
        self.payment_line_ids = [(0, 0, vals) for vals in related_lines_vals]  # Add new lines


    def action_post(self):
        for rec in self:
            super(AccountPayment, rec).action_post()
            # Define the domain based on payment type
            if rec.payment_type == 'inbound':  # Customer payment
                domain = [
                    ('partner_id', '=', rec.partner_id.id),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                    ('move_type', '=', 'out_invoice')]
            elif rec.payment_type == 'outbound':
                domain = [
                    ('partner_id', '=', rec.partner_id.id),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                    ('move_type', '=', 'in_invoice')  # Vendor Bills
                ]
            moves = self.env['account.move'].search(domain, order='id asc')
            if moves:
                for inv in moves:
                    # Find payment line and invoice/bill line
                    payment_lines = rec.move_id.line_ids.filtered(
                        lambda line: line.account_id.reconcile and not line.reconciled
                    )
                    invoice_lines = inv.line_ids.filtered(
                        lambda line: line.account_id.reconcile and not line.reconciled
                    )
                    # Reconcile payment lines with invoice lines
                    for payment_line in payment_lines:
                        matching_lines = invoice_lines.filtered(
                            lambda inv_line: inv_line.account_id == payment_line.account_id
                        )
                        if matching_lines:
                            (payment_line + matching_lines).reconcile()

            for line in rec.payment_line_ids:
                line.status = line.move_id.payment_state
                # line.amount_total = line.move_id.amount_total
                line.amount = line.move_id.amount_residual
                line.paid_amount = line.amount_total - line.amount

        return True


class AccountPaymentLines(models.Model):
    _name = "account.payment.lines"
    _description = "account.payment.lines"

    move_id = fields.Many2one('account.move')
    account_payment_id = fields.Many2one('account.payment')
    amount_total = fields.Float(string="Total Amount")
    amount = fields.Float(string="Balance Amount")
    paid_amount = fields.Float(string="Paid Amount")
    status = fields.Selection(
        [('not_paid', 'Not Paid'), ('in_payment', 'In Payment'), ('paid', 'Paid'), ('partial', 'Partial'),
         ('reversed', 'Reversed'), ('invoicing_legacy', 'Invoicing Legacy')],
        string="Payment Status")
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Posted'), ('cancel', 'Cancel')],
        string="State")

    @api.onchange('amount')
    def _onchange_of_amount(self):
        if self.amount > self.amount_total:
            raise ValidationError("Amount is greater")





