from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from odoo.tools import formatLang
from datetime import datetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            partner_id = order.partner_id.commercial_partner_id
            error_messages = []
            company = order.company_id
            # Fetch Global Days Limit from Settings
            global_days_limit = int(
                self.env['ir.config_parameter'].sudo().get_param(
                    'credit_management.days_limit', 
                    default=0
                )
            )  
            use_credit_limit = company.account_use_credit_limit
            ResPartner = self.env['res.partner']
            global_credit_limit = (
                ResPartner._fields['credit_limit'].get_company_dependent_fallback(ResPartner)
                if use_credit_limit else 0.0
            )
            # Determine Effective Days Limit (Customer-specific takes precedence)
            effective_days_limit = partner_id.days_limit if partner_id.credit_approval_state == 'approved' else global_days_limit
            # ** Days Limit Validation **
            if effective_days_limit:
                # Fetch the last posted invoice for the customer
                invoice = self.env['account.move'].search([
                    ('partner_id', '=', partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted')
                ], order='invoice_date desc', limit=1) 
                if invoice and invoice.invoice_date:
                    days_diff = (datetime.today().date() - invoice.invoice_date).days
                    if days_diff > effective_days_limit:
                        error_messages.append(
                            f"- The customer has exceeded the days limit of {effective_days_limit} days "
                            f"since their last invoice date ({invoice.invoice_date})."
                        ) 
            effective_credit_limit = (
                partner_id.credit_limit
                if partner_id.credit_limit and partner_id.credit_approval_state == 'approved' # If contact has a credit limit set
                else global_credit_limit    # Otherwise use global limit
            )
            # Calculate total credit
            credit_to_invoice = partner_id.credit_to_invoice
            current_amount = order.amount_total
            total_credit = partner_id.credit + credit_to_invoice + current_amount
            # Validate Credit Limit
            if effective_credit_limit and total_credit > effective_credit_limit:
                total_credit_formatted = formatLang(
                    self.env, total_credit, currency_obj=order.company_id.currency_id
                )
                effective_credit_limit_formatted = formatLang(
                    self.env, effective_credit_limit, currency_obj=order.company_id.currency_id
                )
                error_messages.append(
                    _(
                        '- %(partner_name)s has exceeded the credit limit of: %(credit_limit)s. '
                        'Total amount due: %(total_credit)s.',
                        partner_name=partner_id.name,
                        credit_limit=effective_credit_limit_formatted,
                        total_credit=total_credit_formatted
                    )
                )
            if error_messages:
                raise ValidationError("\n".join(error_messages))
            return super(SaleOrder, self).action_confirm()


