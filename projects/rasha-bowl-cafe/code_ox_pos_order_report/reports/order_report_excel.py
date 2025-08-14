from odoo import models
import xlsxwriter

class PosOrderReportXlsx(models.AbstractModel):
    _name = "report.code_ox_pos_order_report.pos_order_report_xlsx"
    _description = "POS Order Excel Report"
    _inherit = "report.report_xlsx.abstract"

    def get_order_report_lines(self, data):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        customer_type = data.get('customer_type')
        order_type_ids = data.get('order_type_ids')
        partner_ids = data.get('partner_ids') or []

        domain = [('date_order', '>=', date_from), 
                  ('date_order', '<=', date_to),
                  ('state', 'in', ['paid', 'invoiced', 'done'])]

        if customer_type:
            domain.append(('customer_type', '=', customer_type))
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))
        if order_type_ids:
            domain.append(('pos_order_type_id', 'in', order_type_ids))

        orders = self.env['pos.order'].search(domain)
        partner_names = [p.name for p in self.env['res.partner'].browse(partner_ids)] if partner_ids else []
        
        report_lines = []
        for order in orders:
            report_lines.append({
                'customer': order.partner_id.name or 'N/A',
                'customer_type': dict([
                    ('walk_in_customer', 'Walk-in Customer'),
                    ('hotel_customer', 'Hotel Customer'),
                    ('complementary_customer', 'Complementary Customer')
                ]).get(order.customer_type, 'N/A'),
                'customer_count': order.customer_count or 0,
                'order_type': order.pos_order_type_id.name or 'N/A',
                'amount_paid': order.amount_paid or 0.0
            })
        
        return report_lines, partner_names

    def generate_xlsx_report(self, workbook, data, orders):
        sheet = workbook.add_worksheet("POS Orders")
        bold = workbook.add_format({'bold': True, 'align': 'center', 'border': 1, 'bg_color': '#D3D3D3'})
        text = workbook.add_format({'align': 'left', 'border': 1})
        number = workbook.add_format({'align': 'right', 'border': 1, 'num_format': '#,##0.00'})

        sheet.merge_range('A1:E1', "POS Order Report", bold)
        sheet.write('A2', "From Date:", bold)
        sheet.write('B2', orders.date_from.strftime('%d-%m-%Y'))
        sheet.write('A3', "To Date:", bold)
        sheet.write('B3', orders.date_to.strftime('%d-%m-%Y'))
        
        if data.get('customer_type'):
            sheet.write('A4', "Customer Type:", bold)
            sheet.write('B4', dict([
                ('walk_in_customer', 'Walk-in Customer'),
                ('hotel_customer', 'Hotel Customer'),
                ('complementary_customer', 'Complementary Customer')
            ]).get(data.get('customer_type'), ''))
        
        report_lines, partner_names = self.get_order_report_lines(data)
        if partner_names:
            sheet.write('A5', "Selected Customers:", bold)
            sheet.write('B5', ", ".join(partner_names))
        
        headers = ["Customer", "Customer Type", "Customer Count", "Order Type", "Amount Paid"]
        for col_num, header in enumerate(headers):
            sheet.write(6, col_num, header, bold)

        row = 7
        
        for line in report_lines:
            sheet.write(row, 0, line['customer'], text)
            sheet.write(row, 1, line['customer_type'], text)
            sheet.write(row, 2, line['customer_count'], number)
            sheet.write(row, 3, line['order_type'], text)
            sheet.write(row, 4, line['amount_paid'], number)
            row += 1

        sheet.set_column('A:E', 20)
        