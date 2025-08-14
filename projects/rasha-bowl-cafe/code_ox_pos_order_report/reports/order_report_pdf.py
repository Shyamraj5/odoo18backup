from odoo import models, api
from datetime import datetime

class PosOrderReport(models.AbstractModel):
    _name = 'report.code_ox_pos_order_report.pos_order_report_template'
    _description = 'POS Order PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        start_date = data.get('date_from')
        end_date = data.get('date_to')
        customer_type = data.get('customer_type')
        order_type_ids = data.get('order_type_ids')

        partner_ids = data.get('partner_ids') or []  

        domain = [('date_order', '>=', start_date),
                  ('date_order', '<=', end_date),
                  ('state', 'in', ['paid', 'invoiced', 'done'])]

        if customer_type:
            domain.append(('customer_type', '=', customer_type))
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))
        if order_type_ids:
            domain.append(('pos_order_type_id', 'in', order_type_ids))


        orders = self.env['pos.order'].search(domain)

        partner_names = [p.name for p in self.env['res.partner'].browse(partner_ids)] if partner_ids else []
        company = self.env.company

        formatted_start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y') if start_date else ''
        formatted_end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d-%m-%Y') if end_date else ''

        return {
            'data': data,
            'doc_ids': orders.ids,
            'docs': orders,
            'date_from': formatted_start_date,
            'date_to': formatted_end_date,
            'customer_type': customer_type if customer_type else False,
            'partner_names': partner_names,
            'company': company,
        }