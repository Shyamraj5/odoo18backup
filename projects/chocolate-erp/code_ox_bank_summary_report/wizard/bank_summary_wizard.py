from odoo import models, fields, _, api

class CompanyBalanceWizard(models.TransientModel):
    _name = 'bank.summary.wizard'
    _description = 'Bank Summary Wizard'

    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.context_today)
    target_move = fields.Selection([('posted', 'Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', required=True,
                                   default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                   default=lambda self: self.env['account.journal'].search([]))

    def _get_default_account_ids(self):
        journals = self.env['account.journal'].search([('type', '=', 'bank')])
        accounts = self.env['account.account']
        for journal in journals:
            if journal.default_account_id.id:
                accounts += journal.default_account_id
            for acc_out in journal.outbound_payment_method_line_ids:
                if acc_out.payment_account_id:
                    accounts += acc_out.payment_account_id
            for acc_in in journal.inbound_payment_method_line_ids:
                if acc_in.payment_account_id:
                    accounts += acc_in.payment_account_id
        return accounts
     
    account_ids = fields.Many2many('account.account',
                                      'Accounts', default=_get_default_account_ids)

    def print_bank_report(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'account_ids':self.account_ids.ids,
            'journal_ids':self.journal_ids.ids,
            'target_moves':self.target_move

        }
        return self.env.ref('code_ox_bank_summary_report.action_bank_summary_report').report_action(self, data=data)