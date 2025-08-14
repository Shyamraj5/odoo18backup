from odoo import models, fields,api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    account_payment_reconcile_id = fields.Many2one('account.payment')


    # automates the reconciliation of payments with selected invoices
    def action_payment_reconcile(self):
        for rec in self:
            # Check if invoices are selected
            selected_invoices = self.env.context.get('active_ids', [])
            if not selected_invoices:
                raise UserError('Please select invoices to reconcile.')

            # Loop through each selected invoice
            for invoice_id in selected_invoices:
                print('rec.account_payment_reconcile_id',rec.account_payment_reconcile_id)
                invoice = self.env['account.move'].browse(invoice_id)
                credit_line = (rec.account_payment_reconcile_id.move_id.line_ids + invoice.line_ids).filtered(lambda line: line.account_id.reconcile and not line.reconciled)

                print(rec.account_payment_reconcile_id.move_id.line_ids,"rec.account_payment_reconcile_id.move_id.line_ids") # Perform reconciliation
                print("invoice.line_ids",invoice.line_ids)
                if credit_line:
                    credit_line.reconcile()


