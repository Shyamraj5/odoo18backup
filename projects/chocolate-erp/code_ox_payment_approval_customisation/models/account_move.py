from odoo import fields, models, _,api
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection_add=[('to_approve', ' To Approve'), ('pending', 'Pending'), ('authorized', 'Authorized'),
                       ('done', 'Approved')],
        ondelete={'to_approve': 'set default',
                  'pending': 'set default',
                  'authorized': 'set default',
                  'done': 'set default'})
    account_payment_count = fields.Integer(string='Account Payment Count', compute='_compute_account_payment_count')
    is_paid = fields.Boolean(string="Paid")

    # @api.depends()
    # def _compute_name(self):
    #     value= super(AccountMove, self)._compute_name()
    #     for each in self:
    #         if each.state == 'draft':
    #             each._set_next_sequence() 
    #     return value
    def _get_payment_journal_data(self):
        move = self
        payments_widget_vals = {'title': _('Less Payment'), 'outstanding': False, 'content': []}

        if move.state == 'posted' and move.is_invoice(include_receipts=True):
            reconciled_vals = []
            reconciled_partials = move.sudo()._get_all_reconciled_invoice_partials()
            for reconciled_partial in reconciled_partials:
                counterpart_line = reconciled_partial['aml']
                if counterpart_line.move_id.ref:
                    reconciliation_ref = '%s (%s)' % (counterpart_line.move_id.name, counterpart_line.move_id.ref)
                else:
                    reconciliation_ref = counterpart_line.move_id.name
                if counterpart_line.amount_currency and counterpart_line.currency_id != counterpart_line.company_id.currency_id:
                    foreign_currency = counterpart_line.currency_id
                else:
                    foreign_currency = False
                reconciled_vals.append({
                    'name': counterpart_line.name,
                    'journal_name': counterpart_line.journal_id.name,
                    'company_name': counterpart_line.journal_id.company_id.name if counterpart_line.journal_id.company_id != move.company_id else False,
                    'amount': reconciled_partial['amount'],
                    'currency_id': move.company_id.currency_id.id if reconciled_partial['is_exchange'] else reconciled_partial['currency'].id,
                    'date': counterpart_line.date,
                    'partial_id': reconciled_partial['partial_id'],
                    'account_payment_id': counterpart_line.payment_id.id,
                    'payment_method_name': counterpart_line.payment_id.payment_method_line_id.name,
                    'move_id': counterpart_line.move_id.id,
                    'ref': reconciliation_ref,
                    # these are necessary for the views to change depending on the values
                    'is_exchange': reconciled_partial['is_exchange'],
                    # 'amount_company_currency': formatLang(self.env, abs(counterpart_line.balance), currency_obj=counterpart_line.company_id.currency_id),
                    # 'amount_foreign_currency': foreign_currency and formatLang(self.env, abs(counterpart_line.amount_currency), currency_obj=foreign_currency)
                })
            payments_widget_vals['content'] = reconciled_vals

        return payments_widget_vals

    def _get_account_payment(self, account_move_id):
        # journal_data = account_move_id._get_payment_journal_data()
        # journal_data = account_move_id.invoice_payments_widget
        # payment_move_ids_list = []
        # payment_ids = self.env['account.payment']
        # if journal_data and isinstance(journal_data, dict):
        #     journal_data_content = journal_data.get('content', False)
        #     for journal_data in journal_data_content:
        #         move_id = journal_data.get('move_id', False)
        #         if move_id:
        #             payment_move_ids_list.append(move_id)
        # if payment_move_ids_list:
        #     payment_move_ids = self.env['account.move'].browse(payment_move_ids_list)
        #     payment_ids = payment_move_ids.mapped('payment_id')
        
        # Commented by Shayar 
        # payment_ids = self.env['account.payment'].search([('bi_account_move_id', '=', account_move_id.id)])
        # return payment_ids
        pass

    def _compute_account_payment_count(self):
        for rec in self:
            account_payment_ids = self._get_account_payment(rec)
            if account_payment_ids:
                rec.account_payment_count = len(account_payment_ids)
            else:
                rec.account_payment_count = 0

    def action_view_account_payment(self):
        self.ensure_one()
        account_payment_ids = self._get_account_payment(self)
        result = self.env['ir.actions.act_window']._for_xml_id('account.action_account_payments_payable')
        if len(account_payment_ids) > 1:
            result['domain'] = [('id', 'in', account_payment_ids.ids)]
        elif len(account_payment_ids) == 1:
            result['views'] = [(self.env.ref('account.view_account_payment_form', False).id, 'form')]
            result['res_id'] = account_payment_ids.id
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
