from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_id = fields.Many2one('account.move', string="Invoice")

    def action_post(self):
        branch_move = False
        for move in self:
            if move.move_type == 'out_invoice':
                branch_sale_margin = 0.0
                source_branch_entry = []
                for line in move.invoice_line_ids:
                    for sale_line in line.sale_line_ids:
                        if sale_line.product_id and sale_line.lot_id and sale_line.lot_id.is_branch_sale:
                            branch_sale_margin += (sale_line.lot_id.margin * line.quantity)
                            # Find if source branch already exists in the list
                            found = False
                            for entry in source_branch_entry:
                                if entry['source_branch'] == sale_line.lot_id.source_branch_id:
                                    entry['margin'] += sale_line.lot_id.margin * line.quantity
                                    found = True
                                    break
                            
                            # If not found, append new entry
                            if not found:
                                source_branch_entry.append({
                                    'source_branch': sale_line.lot_id.source_branch_id,
                                    'margin': sale_line.lot_id.margin * line.quantity
                                })


                if branch_sale_margin > 0:
                    suspense_account_id = move.company_id.branch_suspense_account_id
                    transfer_cost_account_id = move.company_id.branch_transfer_cost_account_id

                    self.env['account.move.line'].create([
                        {
                            'move_id': move.id,
                            'name': 'Branch Suspense',
                            'account_id': suspense_account_id.id,
                            'credit': branch_sale_margin,
                            'debit': 0.0,
                            'partner_id': move.partner_id.id,
                            'company_id': move.company_id.id,
                            'date': move.date,
                            'display_type': 'margin',
                        },
                        {
                            'move_id': move.id,
                            'name': 'Branch Transfer Cost',
                            'account_id': transfer_cost_account_id.id,
                            'credit': 0.0,
                            'debit': branch_sale_margin,
                            'partner_id': move.partner_id.id,
                            'company_id': move.company_id.id,
                            'date': move.date,
                            'display_type': 'margin',
                        }
                    ])
                    # Create inter-branch profit entries
                    for entry in source_branch_entry:
                        ref = move.name
                        branch_move = self.env['account.move'].sudo().create({
                            'ref': f'Inter-branch profit from {ref}',
                            'date': move.date,
                            'journal_id': self.env['account.journal'].search([('name', '=', 'Miscellaneous Operations')], limit=1).id,
                            'company_id': entry['source_branch'].id,
                            'invoice_id': move.id,
                            'line_ids': [
                                (0, 0, {
                                    'name': 'Unrealised Branch Profit',
                                    'account_id': entry['source_branch'].unrealized_branch_profit_account_id.id,
                                    'debit': entry['margin'],
                                    'credit': 0.0,
                                }),
                                (0, 0, {
                                    'name': 'Branch Profit',
                                    'account_id': entry['source_branch'].inter_branch_profit_account_id.id,
                                    'debit': 0.0,
                                    'credit': entry['margin'],
                                })
                            ]
                        })
                        branch_move.action_post()
        res = super(AccountMove, self).action_post()
        if branch_move:
            branch_move.ref = f'Inter-branch profit from {self.name}'
        return res
    

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        for move in self:
            if move.move_type == 'out_invoice':
                # Remove the branch sale margin entries
                move.line_ids.filtered(lambda l: l.display_type == 'margin').unlink()
                move.line_ids.filtered(lambda l: l.display_type == 'margin').unlink()
                
                # Remove inter-branch profit entries
                inter_branch_moves = self.env['account.move'].search([('invoice_id', '=', move.id)])
                inter_branch_moves.button_draft()
                inter_branch_moves.unlink()
        return res