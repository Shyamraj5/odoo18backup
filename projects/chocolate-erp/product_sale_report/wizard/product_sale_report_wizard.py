from odoo import models, fields, _

class ProductSaleReportWizard(models.TransientModel):
    _name = 'product.sale.report.wizard'
    _description = 'Product Sale Report Wizard'

    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True)

    def generate_xlsx_report(self):
        domain = [
            ('date_order', '>=', self.date_from),
            ('date_order', '<=', self.date_to),
            ('state', 'not in', ['draft', 'cancel']),
            ('invoice_status', '=', 'invoiced')
        ]
        
        sale_orders = self.env['sale.order'].search(domain)
        
        report_data = []
        total_quantity = 0
        total_unit_price = 0
        total_gross = 0
        total_discount = 0
        total_vat = 0
        total_net = 0
        total_margin = 0
        
        for order in sale_orders:
            posted_invoices = order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            if not posted_invoices:
                continue
                
            invoice_number = ', '.join(posted_invoices.mapped('name'))
            
            for line in order.order_line:
                vals = {
                    'date': order.date_order,
                    'invoice_number': invoice_number,
                    'partner_name': order.partner_id.name,
                    'product_code': line.product_id.default_code or '',
                    'batch_code': line.lot_id.name if line.lot_id else '',
                    'product_name': line.product_id.name,
                    'quantity': line.product_uom_qty,
                    'uom': line.product_uom.name if line.product_uom else '',
                    'unit_price': line.price_unit,
                    'gross': line.price_subtotal,
                    'discount': line.discount,
                    'vat': line.price_tax if line.price_tax else 0,
                    'net_amount':line.price_total,
                    'cost': '',
                    'margin': line.margin
                }
                report_data.append(vals)
                
                total_quantity += line.product_uom_qty
                total_unit_price += line.price_unit
                total_gross += line.price_subtotal
                total_discount += line.discount
                total_vat += line.price_tax if line.price_tax else 0
                total_net += line.price_total if line.price_total else 0
                total_margin += line.margin

        totals = {
            'total_quantity': total_quantity,
            'total_unit_price': total_unit_price,
            'total_gross': total_gross,
            'total_discount': total_discount,
            'total_vat': total_vat,
            'total_net':total_net,
            'total_margin': total_margin
        }

        return self.env.ref('product_sale_report.action_sale_xlsx_report').report_action(
            self, data={'report_data': report_data, 'totals': totals}
        )