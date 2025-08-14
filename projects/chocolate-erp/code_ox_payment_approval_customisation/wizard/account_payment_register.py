# -*- coding: utf-8 -*-

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # def _reconcile_payments_after_approve(self, payment_id, edit_mode=False):
    #     """ Reconcile the payments. After Third approval
    #
    #     :param to_process:  A list of python dictionary, one for each payment to create, containing:
    #                         * create_vals:  The values used for the 'create' method.
    #                         * to_reconcile: The journal items to perform the reconciliation.
    #                         * batch:        A python dict containing everything you want about the source journal items
    #                                         to which a payment will be created (see '_get_batches').
    #     :param edit_mode:   Is the wizard in edition mode.
    #     """
    #     # Get Payment
    #     self.ensure_one()
    #     all_batches = self._get_batches()
    #     print('all_batches:::', all_batches)
    #     batches = []
    #     # Skip batches that are not valid (bank account not trusted but required)
    #     for batch in all_batches:
    #         batch_account = self._get_batch_account(batch)
    #         if self.require_partner_bank_account and not batch_account.allow_out_payment:
    #             continue
    #         batches.append(batch)
    #
    #     if not batches:
    #         raise UserError(_('To record payments with %s, the recipient bank account must be manually validated. You should go on the partner bank account in order to validate it.', self.payment_method_line_id.name))
    #
    #     line_ids = batches[0]['lines']
    #
    #     domain = [
    #         ('parent_state', '=', 'posted'),
    #         ('account_type', 'in', self.env['account.payment']._get_valid_payment_account_types()),
    #         ('reconciled', '=', False),
    #     ]
    #     payment_lines = payment_id.line_ids.filtered_domain(domain)
    #     for account in payment_lines.account_id:
    #         (payment_lines + line_ids) \
    #             .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
    #
    #     # for vals in to_process:
    #     #     payment_lines = vals['payment'].line_ids.filtered_domain(domain)
    #     #     lines = vals['to_reconcile']
    #     #
    #     #     for account in payment_lines.account_id:
    #     #         (payment_lines + lines)\
    #     #             .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)])\
    #     #             .reconcile()

    def action_create_payments(self):
        payments = self._create_payments()
        account_move_id = self.line_ids and self.line_ids.mapped('move_id')[0]
        for payment_id in payments:
            if payment_id.payment_type and payment_id.payment_type=='outbound':
                account_move_id = self.line_ids.move_id.filtered(lambda x: x.display_name == payment_id.memo)
                # payment_id.bi_account_move_id = account_move_id and account_move_id.id or False
                payment_id.bi_account_move_id = account_move_id.id
                payment_id.action_draft()
        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', payments.ids)],
            })

        return action
