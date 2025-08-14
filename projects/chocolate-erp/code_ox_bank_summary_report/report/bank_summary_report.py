from odoo import models,api

class ReportCompanyBalance(models.AbstractModel):
    _name = 'report.code_ox_bank_summary_report.bank_summary_report'
    _description = 'Company Balance Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            return {}

        # Get data from form
        date_from = data.get('form', {}).get('date_from') or data.get('date_from')
        date_to = data.get('form', {}).get('date_to') or data.get('date_to')
        account_ids = data.get('account_ids')
        journal_ids = data.get('journal_ids')
        target_move = data.get('target_move', 'posted')

        current_user = self.env.user
        companies = current_user.company_ids
        balances = []

        for company in companies:
            query = """
                SELECT SUM(debit) - SUM(credit) AS balance
                FROM account_move_line
                WHERE company_id = %s
                AND account_id IN %s
                AND date BETWEEN %s AND %s
                {journal_filter}
                {move_filter}
            """

            journal_filter = "AND journal_id IN %s" if journal_ids else ""

            move_filter = "AND parent_state = 'posted'" if target_move == 'posted' else ""

            query = query.format(journal_filter=journal_filter, move_filter=move_filter)

            params = [company.id, tuple(account_ids), date_from, date_to]
            if journal_ids:
                params.append(tuple(journal_ids))

            self.env.cr.execute(query, params)
            result = self.env.cr.fetchone() 

            balance = result[0] if result and result[0] else 0.0

            balances.append({
                'company_name': company.name,
                'balance': balance,
                'currency_id': company.currency_id.id
            })

        wizard = self.env['bank.summary.wizard'].browse(docids[0]) if docids else False

        return {
            'doc_ids': docids,
            'doc_model': 'bank.summary.wizard',
            'docs': wizard,
            'data': data,
            'balances': balances,
            'date_from': date_from,
            'date_to': date_to
        }