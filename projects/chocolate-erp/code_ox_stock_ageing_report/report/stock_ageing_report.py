from odoo import models
from datetime import datetime, timedelta

class StockAgeingReport(models.AbstractModel):
    _name = 'report.code_ox_stock_ageing_report.report_stock_ageing'
    _description = 'Stock Ageing Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('Stock Ageing Report')

        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        cell_format = workbook.add_format({
            'align': 'left',
            'border': 1
        })

        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'border': 1
        })
        sheet.merge_range('A1:P1', "Stock Ageing Report", header_format)
        sheet.write(1, 0, 'As on Date', cell_format)
        sheet.merge_range(1, 1, 1, 5, lines.date.strftime('%d-%m-%Y'), cell_format)
        head_row = 2
        if lines.product_id:
            head_row += 1
            sheet.write(2, 0, 'Product', cell_format)
            sheet.merge_range(2, 1, 2, 5, lines.product_id.display_name, cell_format)
        locations = self.env['stock.location'].search([('usage', '=', 'internal'), ('company_id', '=', self.env.company.id)])
        if lines.warehouse_id:
            locations = self.env['stock.location'].search([('usage', '=', 'internal'), ('warehouse_id', '=', lines.warehouse_id.id)])
            head_row += 1
            sheet.write(3, 0, 'Warehouse', cell_format)
            sheet.merge_range(3, 1, 3, 5, lines.warehouse_id.display_name, cell_format)
        sheet.merge_range(head_row, 0, head_row+1, 0, 'Purchase Date', header_format)
        sheet.merge_range(head_row, 1, head_row+1, 1, 'Product', header_format)
        sheet.merge_range(head_row, 2, head_row+1, 2, 'Purchase Supplier', header_format)
        sheet.merge_range(head_row, 3, head_row+1, 3, 'Purchase Quantity', header_format)
        sheet.merge_range(head_row, 4, head_row+1, 4, 'Lot No', header_format)
        sheet.merge_range(head_row, 5, head_row, 6, 'Sales', header_format)
        sheet.write(head_row+1, 5, 'Last 60 Days', header_format)
        sheet.write(head_row+1, 6, 'Last 30 Days', header_format)
        sheet.merge_range(head_row, 7, head_row, 11, 'To be Expired', header_format)
        sheet.write(head_row+1, 7, 'in 30 Days', header_format)
        sheet.write(head_row+1, 8, 'in 60 Days', header_format)
        sheet.write(head_row+1, 9, 'in 90 Days', header_format)
        sheet.write(head_row+1, 10, 'in 120 Days', header_format)
        sheet.write(head_row+1, 11, 'in 150+ Days', header_format)
        sheet.merge_range(head_row, 12, head_row+1, 12, 'Closing Stock', header_format)
        sheet.merge_range(head_row, 13, head_row+1, 13, 'Expiry Date', header_format)
        sheet.merge_range(head_row, 14, head_row+1, 14, 'No of days left', header_format)
        sheet.merge_range(head_row, 15, head_row+1, 15, 'Location', header_format)

        domain = []
        if lines.product_id:
            domain.append(('product_id', '=', lines.product_id.id))
        product_lots = self.env['stock.lot'].search(domain, order='product_id, create_date')
        row = head_row + 2
        tot_last_60_days_qty = 0
        tot_last_30_days_qty = 0
        tot_qty = 0
        tot_qty_in_30_days = 0
        tot_qty_in_60_days = 0
        tot_qty_in_90_days = 0
        tot_qty_in_120_days = 0
        tot_qty_in_150_days = 0
        for lot in product_lots:
            supplier = lot.purchase_order_ids[0].partner_id.name if lot.purchase_order_ids else False
            purchase_date = lot.purchase_order_ids[0].date_approve if lot.purchase_order_ids else False
            purchase_qty = sum(lot.purchase_order_ids.mapped('order_line').filtered(lambda x: x.product_id == lot.product_id).mapped('qty_received'))
            expiry_date = lot.expiration_date.date() if lot.expiration_date else False
            days_left = (expiry_date - lines.date).days if expiry_date else False
            if lot.location_id:
                if lot.location_id not in locations:
                    continue
                last_60_days_qty = sum(lot.sale_order_ids.filtered(lambda x: x.date_order.date() >= lines.date - timedelta(days=60) and x.invoice_status == 'invoiced').mapped('order_line').filtered(lambda x: x.product_id == lot.product_id).mapped('product_uom_qty'))
                last_30_days_qty = sum(lot.sale_order_ids.filtered(lambda x: x.date_order.date() >= lines.date - timedelta(days=30) and x.invoice_status == 'invoiced').mapped('order_line').filtered(lambda x: x.product_id == lot.product_id).mapped('product_uom_qty'))
                tot_last_60_days_qty += last_60_days_qty
                tot_last_30_days_qty += last_30_days_qty
                sheet.write(row, 0, purchase_date.date().strftime('%d-%m-%Y') if purchase_date else '', cell_format)
                sheet.write(row, 1, lot.product_id.name, cell_format)
                sheet.write(row, 2, supplier if supplier else '', cell_format)
                sheet.write(row, 3, purchase_qty, number_format)
                sheet.write(row, 4, lot.name, cell_format)
                sheet.write(row, 5, last_60_days_qty, number_format)
                sheet.write(row, 6, last_30_days_qty, number_format)
                sheet.write(row, 7, '', number_format)
                sheet.write(row, 8, '', number_format)
                sheet.write(row, 9, '', number_format)
                sheet.write(row, 10, '', number_format)
                sheet.write(row, 11, '', number_format)
                qty = lot.product_id.with_context(to_date=lines.date, lot_id=lot.id, location=lot.location_id.id).qty_available
                tot_qty += qty
                if days_left <= 30:
                    sheet.write(row, 7, qty, number_format)
                    tot_qty_in_30_days += qty
                elif days_left <= 60 and days_left > 30:
                    sheet.write(row, 8, qty, number_format)
                    tot_qty_in_60_days += qty
                elif days_left <= 90 and days_left > 60:
                    sheet.write(row, 9, qty, number_format)
                    tot_qty_in_90_days += qty
                elif days_left <= 120 and days_left > 90:
                    sheet.write(row, 10, qty, number_format)
                    tot_qty_in_120_days += qty
                else:
                    sheet.write(row, 11, qty, number_format)
                    tot_qty_in_150_days += qty
                sheet.write(row, 12, qty, number_format)
                sheet.write(row, 13, expiry_date.strftime('%d-%m-%Y') if expiry_date else '', cell_format)
                sheet.write(row, 14, days_left, number_format)
                sheet.write(row, 15, lot.location_id.display_name, cell_format)
                row += 1
            else:
                quant_ids = lot.quant_ids.filtered(lambda x: x.location_id.usage == 'internal')
                for quant in quant_ids:
                    if quant.location_id not in locations:
                        continue
                    last_60_days_qty = sum(lot.sale_order_ids.filtered(lambda x: x.date_order.date() >= lines.date - timedelta(days=60) and x.invoice_status == 'invoiced').mapped('order_line').filtered(lambda x: x.product_id == lot.product_id).mapped('product_uom_qty'))
                    last_30_days_qty = sum(lot.sale_order_ids.filtered(lambda x: x.date_order.date() >= lines.date - timedelta(days=30) and x.invoice_status == 'invoiced').mapped('order_line').filtered(lambda x: x.product_id == lot.product_id).mapped('product_uom_qty'))
                    tot_last_60_days_qty += last_60_days_qty
                    tot_last_30_days_qty += last_30_days_qty
                    sheet.write(row, 0, purchase_date.date().strftime('%d-%m-%Y') if purchase_date else '', cell_format)
                    sheet.write(row, 1, lot.product_id.name, cell_format)
                    sheet.write(row, 2, supplier if supplier else '', cell_format)
                    sheet.write(row, 3, purchase_qty, number_format)
                    sheet.write(row, 4, lot.name, cell_format)
                    sheet.write(row, 5, last_60_days_qty, number_format)
                    sheet.write(row, 6, last_30_days_qty, number_format)
                    sheet.write(row, 7, '', number_format)
                    sheet.write(row, 8, '', number_format)
                    sheet.write(row, 9, '', number_format)
                    sheet.write(row, 10, '', number_format)
                    sheet.write(row, 11, '', number_format)
                    qty = lot.product_id.with_context(to_date=lines.date, lot_id=lot.id, location=quant.location_id.id).qty_available
                    tot_qty += qty
                    if days_left <= 30:
                        sheet.write(row, 7, qty, number_format)
                        tot_qty_in_30_days += qty
                    elif days_left <= 60 and days_left > 30:
                        sheet.write(row, 8, qty, number_format)
                        tot_qty_in_60_days += qty
                    elif days_left <= 90 and days_left > 60:
                        sheet.write(row, 9, qty, number_format)
                        tot_qty_in_90_days += qty
                    elif days_left <= 120 and days_left > 90:
                        sheet.write(row, 10, qty, number_format)
                        tot_qty_in_120_days += qty
                    else:
                        sheet.write(row, 11, qty, number_format)
                        tot_qty_in_150_days += qty
                    sheet.write(row, 12, qty, number_format)
                    sheet.write(row, 13, expiry_date.strftime('%d-%m-%Y') if expiry_date else '', cell_format)
                    sheet.write(row, 14, days_left, number_format)
                    sheet.write(row, 15, quant.location_id.display_name, cell_format)
                    row += 1
        
        sheet.write(row, 5, tot_last_60_days_qty, number_format)
        sheet.write(row, 6, tot_last_30_days_qty, number_format)
        sheet.write(row, 7, tot_qty_in_30_days, number_format)
        sheet.write(row, 8, tot_qty_in_60_days, number_format)
        sheet.write(row, 9, tot_qty_in_90_days, number_format)
        sheet.write(row, 10, tot_qty_in_120_days, number_format)
        sheet.write(row, 11, tot_qty_in_150_days, number_format)
        sheet.write(row, 12, tot_qty, number_format)
        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 10)
        sheet.set_column(4, 4, 10)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 25)