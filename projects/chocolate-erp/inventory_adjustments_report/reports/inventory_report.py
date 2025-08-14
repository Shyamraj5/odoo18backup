from odoo import models
from datetime import datetime

class PurchaseExcelReport(models.AbstractModel):
    _name = 'report.inventory_adjustments_report.inventory_report'
    _description = 'Inventory Adjustments Report'
    _inherit = "report.report_xlsx.abstract"

    def get_purchase_report_lines(self, data):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        current_company_id = self.env.company.id
        stock_location_id = data.get('stock_location_id')
        stock_location = self.env['stock.location'].browse(stock_location_id)
        domain = [
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('state', '=', 'done'),
            '|',
            '&',
                ('location_id.usage', '=', 'inventory'),
                ('location_id.scrap_location', '=', False),
            '&',
                ('location_dest_id.usage', '=', 'inventory'),
                ('location_dest_id.scrap_location', '=', False)
        ]

        if stock_location:
            domain.append('|')
            domain.append(('location_id', '=', stock_location.id))
            domain.append(('location_dest_id', '=', stock_location.id))

        stock_moves = self.env['stock.move.line'].search(domain)

        report_lines = []
        for lot in stock_moves.mapped('lot_id'):
            lot_moves = stock_moves.filtered(lambda move: move.lot_id == lot)
            locations = (
                lot_moves.mapped('location_id').filtered(lambda loc: loc.usage != 'inventory') |
                lot_moves.mapped('location_dest_id').filtered(lambda loc: loc.usage != 'inventory')
            )
            product = lot.product_id
            for location in locations:
                current_stock = product.with_context(to_date=date_from, location=location.id, lot_id=lot.id).qty_available
                unit_cost = lot.avg_cost

                add_stock = 0
                reduce_stock = 0

                for move in lot_moves:
                    if move.location_dest_id.usage == 'inventory' and move.location_id == location:
                        add_stock += move.quantity
                    elif move.location_id.usage == 'inventory' and move.location_dest_id == location:
                        reduce_stock += move.quantity           

                add_stock_value = add_stock * unit_cost
                reduce_stock_value = reduce_stock * unit_cost
                adjusted_current_stock = current_stock + add_stock - reduce_stock
                stock_value = adjusted_current_stock * unit_cost

                expiry_date = lot.expiration_date if lot.expiration_date else ''
                no_of_days_left = (expiry_date - datetime.now().date()).days if expiry_date else ''

                report_lines.append({
                    'purchase_date': lot.purchase_order_ids[0].date_order if lot.purchase_order_ids else '',
                    'product_code': product.default_code,
                    'product': product.name,
                    'purchase_supplier': '',
                    'current_stock': current_stock,
                    'uom': product.uom_id.name,
                    'lot_no': lot.name if lot else '',
                    'unit_cost': unit_cost,
                    'add_stock': add_stock,
                    'add_stock_value': add_stock_value,
                    'reduce_stock': reduce_stock,
                    'reduce_stock_value': reduce_stock_value,
                    'adjusted_current_stock': adjusted_current_stock,
                    'stock_value': stock_value,
                    'expiry_date': expiry_date,
                    'no_of_days_left': no_of_days_left,
                    'location': location.display_name,
                })

        return report_lines

    def generate_xlsx_report(self, workbook, data, objs):
        sheet = workbook.add_worksheet('Inventory Adjustments Report')

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
        date_format = workbook.add_format({'num_format': 'mm-dd-yyyy', 'align': 'left', 'border': 1})
        header_format = workbook.add_format({
            'bold': True, 'align': 'center',
            'valign': 'vcenter', 'border': 1,
            'bg_color': '#FFFF00'
        })

        headers = [
            'Purchase Date', 'Product Code', 'Product', 'Purchase Supplier', 'Current Stock',
            'UoM', 'Lot No', 'Unit Cost', 'Add Stock', 'Add Stock Value', 'Reduce Stock',
            'Reduce Stock Value', 'Adjusted Current Stock', 'Stock Value', 'Expiry Date', 'No of Days Left', 'Location'
        ]

        report_lines = self.get_purchase_report_lines(data)

        total_add_stock = sum(line['add_stock'] for line in report_lines)
        total_reduce_stock = sum(line['reduce_stock'] for line in report_lines)
        total_add_value = sum(line['add_stock_value'] for line in report_lines)
        total_reduce_value = sum(line['reduce_stock_value'] for line in report_lines)

        # Summary Table
        total_qty = total_add_stock + total_reduce_stock
        total_value = total_add_value + total_reduce_value

        date_to = data.get('date_to')
        location_name = data.get('location_name') if data.get('location_name') else 'No location is selected'
        if isinstance(date_to, str):
            date_to = datetime.strptime(date_to.split()[0], '%Y-%m-%d').date()

        sheet.merge_range('A1:B1', f'As on Date', bold)
        sheet.write('C1', date_to, date_format)
        sheet.merge_range('A2:C2', f'{location_name}', header_format)

        sheet.write('A4', 'Summary', bold)
        sheet.write('B4', 'Qty', bold)
        sheet.write('C4', 'Value', bold)

        sheet.write('A5', 'Add Stock', text)
        sheet.write('B5', total_add_stock, number)
        sheet.write('C5', total_add_value, number)

        sheet.write('A6', 'Reduce Stock', text)
        sheet.write('B6', total_reduce_stock, number)
        sheet.write('C6', total_reduce_value, number)

        sheet.write('A7', 'Total', text)
        sheet.write('B7', total_qty, number)
        sheet.write('C7', total_value, number)

        # Main Table
        for col_num, header in enumerate(headers):
            sheet.write(9, col_num, header, bold)

        for row_num, line in enumerate(report_lines, start=10):
            sheet.write(row_num, 0, line['purchase_date'], date_format)
            sheet.write(row_num, 1, line['product_code'], text)
            sheet.write(row_num, 2, line['product'], text)
            sheet.write(row_num, 3, line['purchase_supplier'], text)
            sheet.write(row_num, 4, line['current_stock'], text)
            sheet.write(row_num, 5, line['uom'], text)
            sheet.write(row_num, 6, line['lot_no'], text)
            sheet.write(row_num, 7, line['unit_cost'], number)
            sheet.write(row_num, 8, line['add_stock'], number)
            sheet.write(row_num, 9, line['add_stock_value'], number)
            sheet.write(row_num, 10, line['reduce_stock'], number)
            sheet.write(row_num, 11, line['reduce_stock_value'], number)
            sheet.write(row_num, 12, line['adjusted_current_stock'], number)
            sheet.write(row_num, 13, line['stock_value'], text)
            sheet.write(row_num, 14, line['expiry_date'], date_format)
            sheet.write(row_num, 15, line['no_of_days_left'], text)
            sheet.write(row_num, 16, line['location'], text)

        sheet.set_column('A:Q', 35)
