from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    branch_transfer_in_line_id = fields.Many2one('branch.transfer.in.line', string="Transfer In Line", help="Link to the transfer line that generated this move.")
    branch_transfer_out_line_id = fields.Many2one('branch.transfer.out.line', string="Transfer Out Line", help="Link to the transfer line that generated this move.")
    def _account_entry_move(self, qty, description, svl_id, cost):
        """ Accounting Valuation Entries """
        self.ensure_one()
        am_vals = []
        if not self.product_id.is_storable:
            # no stock valuation for consumable products
            return am_vals
        if self._should_exclude_for_valuation():
            return am_vals

        move_directions = self.env.context.get('move_directions') or False

        self_is_out_move = self_is_in_move = False
        if move_directions:
            self_is_out_move = move_directions.get(self.id) and 'out' in move_directions.get(self.id)
            self_is_in_move = move_directions.get(self.id) and 'in' in move_directions.get(self.id)
        else:
            self_is_out_move = self._is_out()
            self_is_in_move = self._is_in()

        company_from = self_is_out_move and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self_is_in_move and self.mapped('move_line_ids.location_dest_id.company_id') or False

        if self.picking_id.branch_transfer_in_id or self.picking_id.branch_transfer_out_id:
            journal_id, acc_src, acc_dest, acc_valuation = self.with_context(branch_sale=True)._get_accounting_data_for_valuation()
        else:
            journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self_is_in_move:
            if self._is_returned(valued_type='in'):
                am_vals.append(self.with_company(company_to).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
            else:
                am_vals.append(self.with_company(company_to)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))

        # Create Journal Entry for products leaving the company
        if self_is_out_move:
            cost = -1 * cost
            if self._is_returned(valued_type='out'):
                am_vals.append(self.with_company(company_from).with_context(is_returned=True)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
            else:
                am_vals.append(self.with_company(company_from)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            anglosaxon_am_vals = self._prepare_anglosaxon_account_move_vals(acc_src, acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost)
            if anglosaxon_am_vals:
                am_vals.append(anglosaxon_am_vals)

        return am_vals
    
    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        self = self.with_company(self.company_id)
        if self._context.get('branch_sale'):
            accounts_data = self.product_id.product_tmpl_id.with_context(branch_sale=True).get_product_accounts()
        else:
            accounts_data = self.product_id.product_tmpl_id.get_product_accounts()

        acc_src = self._get_src_account(accounts_data)
        acc_dest = self._get_dest_account(accounts_data)

        acc_valuation = accounts_data.get('stock_valuation', False)
        if acc_valuation:
            acc_valuation = acc_valuation.id
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts.'))
        if not acc_src:
            raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.', self.product_id.display_name))
        if not acc_dest:
            raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.', self.product_id.display_name))
        if not acc_valuation:
            raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest, acc_valuation