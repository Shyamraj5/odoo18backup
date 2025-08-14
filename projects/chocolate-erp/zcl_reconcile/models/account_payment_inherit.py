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

    unpaid_invoice_bill_ids = fields.One2many(
        'account.move',
        string='Unpaid Invoices',
        store=False

    )


    @api.depends('partner_id')
    def _compute_unpaid_moves(self):
        for record in self:
            if record.partner_id:
                # Fetch unpaid invoices and bills in one search
                moves = self.env['account.move'].search([
                    ('partner_id', '=', record.partner_id.id),
                    ('move_type', 'in', ['out_invoice', 'in_invoice']),  # Both Invoices and Bills
                    ('payment_state', '!=', 'paid'),
                    ('state', '=', 'posted')
                ])
                record.unpaid_invoice_bill_ids = moves

                if record.unpaid_invoice_bill_ids:
                    for rec in record.unpaid_invoice_bill_ids:
                        rec.account_payment_reconcile_id = record.id

            else:
                record.unpaid_invoice_bill_ids = False

    def action_view_unpaid_invoices(self):
        self._compute_unpaid_moves()
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unpaid Invoices',
            'view_mode': 'list',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.unpaid_invoice_bill_ids.ids),
                       ('move_type', '=', 'out_invoice')
                       ],
            'target': 'new',  # Opens in a popup
            'context': {
                'create': False,
                'edit': False,
                'default_move_type': 'out_invoice'
            },
            'view_id': self.env.ref('zcl_reconcile.view_account_move_tree_custom').id,  # Reference to custom view
        }

    def action_view_unpaid_bills(self):
        self._compute_unpaid_moves()
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Unpaid Bills',
            'view_mode': 'list',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.unpaid_invoice_bill_ids.ids),
                       ('move_type', '=', 'in_invoice')],
            'target': 'new',
            'context': {
                'create': False,
                'edit': False,
                'default_move_type': 'in_invoice'
            },
            'view_id': self.env.ref('zcl_reconcile.view_account_move_tree_custom').id,

        }







