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

    partner_total_payable = fields.Monetary(compute='_compute_payable_receivable', store=True,
                                            string='Total Receivable', readonly=True,
                                            help="Total amount this customer owes you."
                                            )
    partner_total_receivable = fields.Monetary(compute='_compute_payable_receivable', store=True,
                                               string='Total Payable', readonly=True,
                                               help="Total amount you have to pay to this "
                                                    "vendor.")

    @api.depends('partner_id')
    def _compute_payable_receivable(self):
        for record in self:
            if record.partner_id:
                record.partner_total_payable = record.partner_id.credit
                record.partner_total_receivable = record.partner_id.debit
            else:
                record.partner_total_payable = 0.0
                record.partner_total_receivable = 0.0





