from odoo import models
from datetime import datetime

class PurchaseExcelReport(models.AbstractModel):
    _name = 'report.purchase_excel_report.purchase_report'
    _description = 'Purchase Excel Report'
    _inherit = "report.report_xlsx.abstract"

    def get_purchase_report_lines(self, data):
        date_from = data.get('date_from')
        date_to = data.get('date_to')

        purchases = self.env['purchase.order'].search([
            ('date_order', '>=', date_from),
            ('date_order', '<=', date_to),
            ('state', '=', 'purchase'),
            ('invoice_ids', '!=', False)
        ])

        report_lines = []

        for purchase in purchases:
            for line in purchase.order_line:
                for move in line.move_ids:
                    lots = move.lot_ids if move.lot_ids else [None]
                    for lot in lots:
                        vendor_bill = purchase.invoice_ids.filtered(lambda inv: inv.state == 'posted')
                        for bill in vendor_bill:
                            report_lines.append({
                                'date': bill.invoice_date or '',
                                'ref_no': bill.name or '',
                                'vendor_name': purchase.partner_id.name or '',
                                'product_code': line.internal_reference or '',
                                'batch_code': lot.name if lot else '',
                                'product': line.product_id.name or '',
                                'quantity': line.product_qty or 0,
                                'uom': line.product_uom.name or '',
                                'unit_price': line.price_unit or 0,
                                'gross': line.price_subtotal or 0,
                                'discount': line.discount or 0,
                                'vat': line.price_tax or 0,
                                'net_amount': line.price_total or 0,
                                'purchaser': purchase.user_id.name or ''
                            })

        return report_lines

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet('Purchase Report')

        # Style
        bold = workbook.add_format({
            'bold': True, 'align': 'center',
            'valign': 'vcenter', 'border': 1,
            'bg_color': '#D3D3D3', 'color': 'red'
        })
        text = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1
        })
        number = workbook.add_format({
            'align': 'right', 'valign': 'vcenter',
            'border': 1, 'num_format': '#,##0.00'
        })
        total_numbers = workbook.add_format({
            'align': 'right', 'valign': 'vcenter',
            'border': 1, 'num_format': '#,##0.00', 'bg_color': '#D3D3D3'
        })
        date_format = workbook.add_format({'num_format': 'mm-dd-yyyy', 'align': 'left'})

        headers = [
            'Date', 'Ref No.', 'Vendor Name', 'Product Code', 'Batch Code',
            'Product', 'Quantity', 'UoM', 'Unit Price', 'Gross',
            'Discount', 'VAT', 'Net Amount', 'Cost', 'Total Profit', 'Purchaser'
        ]

        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, bold)

        report_lines = self.get_purchase_report_lines(data)

        total_quantity = 0
        total_unit_price = 0
        total_gross = 0
        total_discount = 0
        total_vat = 0
        total_net_amount = 0

        # Data
        for row_num, line in enumerate(report_lines, start=1):
            sheet.write(row_num, 0, line['date'], date_format)
            sheet.write(row_num, 1, line['ref_no'], text)
            sheet.write(row_num, 2, line['vendor_name'], text)
            sheet.write(row_num, 3, line['product_code'], text)
            sheet.write(row_num, 4, line['batch_code'], text)
            sheet.write(row_num, 5, line['product'], text)
            sheet.write(row_num, 6, line['quantity'], number)
            sheet.write(row_num, 7, line['uom'], text)
            sheet.write(row_num, 8, line['unit_price'], number)
            sheet.write(row_num, 9, line['gross'], number)
            sheet.write(row_num, 10, line['discount'], number)
            sheet.write(row_num, 11, line['vat'], number)
            sheet.write(row_num, 12, line['net_amount'], number)
            sheet.write(row_num, 13, '', text)
            sheet.write(row_num, 14, '', text)
            sheet.write(row_num, 15, line['purchaser'], text)

            # Calculate totals
            total_quantity += line['quantity']
            total_unit_price += line['unit_price']
            total_gross += line['gross']
            total_discount += line['discount']
            total_vat += line['vat']
            total_net_amount += line['net_amount']

        # Totals
        total_row = len(report_lines) + 1
        sheet.write(total_row, 5, 'TOTAL', bold)
        sheet.write(total_row, 6, total_quantity, total_numbers)
        sheet.write(total_row, 7, '', text)
        sheet.write(total_row, 8, total_unit_price, total_numbers)
        sheet.write(total_row, 9, total_gross, total_numbers)
        sheet.write(total_row, 10, total_discount, total_numbers)
        sheet.write(total_row, 11, total_vat, total_numbers)
        sheet.write(total_row, 12, total_net_amount, total_numbers)
        sheet.write(total_row, 13, '', total_numbers)
        sheet.write(total_row, 14, '', total_numbers)
        sheet.write(total_row, 15, '', text)

        # Column width
        sheet.set_column('A:A', 12)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 40)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 40)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:H', 15)
        sheet.set_column('I:I', 12)
        sheet.set_column('J:J', 12)
        sheet.set_column('K:K', 12)
        sheet.set_column('L:L', 12)
        sheet.set_column('M:M', 15)
        sheet.set_column('N:N', 10)
        sheet.set_column('O:O', 15)
        sheet.set_column('P:P',25)
