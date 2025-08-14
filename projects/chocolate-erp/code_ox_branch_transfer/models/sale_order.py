from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    company_partner_ids = fields.Many2many(
        'res.partner', 
        compute='_compute_company_partner_ids', 
        store=True
    )
    
    @api.depends('company_id')
    def _compute_company_partner_ids(self):
        company_partners = self.env['res.company'].sudo().search([('id', '!=', self.env.company.id)]).mapped('partner_id')
        for order in self:
            order.company_partner_ids = company_partners

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        for order in self:
            if order.inter_company:
                moves.inter_company = True
                # Append margin to the invoice
                margin_account = order.company_id.margin_account_id
                if not margin_account:
                    raise UserError(_("Please set profit margin account for the company."))
                for move in moves:
                    margin = order.margin
                    if margin:
                        product = self.env['product.product'].search([('name', '=', 'Margin')], limit=1)
                        margin_line = move.invoice_line_ids.create({
                            'product_id': product.id,
                            'price_unit': margin,
                            'quantity': 1,
                            'name': 'Margin',
                            'move_id': move.id,
                            'display_type': 'product',
                            'is_margin': True,
                            'account_id': margin_account.id,
                            'tax_ids': False
                        })
                        move.invoice_line_ids += margin_line
        return moves
    