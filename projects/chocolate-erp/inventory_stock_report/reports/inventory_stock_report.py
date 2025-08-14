from odoo import models
from datetime import datetime

class InventoryStockReport(models.AbstractModel):
    _name = 'report.inventory_stock_report.stock_report'
    _description = 'Inventory Stock Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        end_date = lines['end_date']
        sheet = workbook.add_worksheet('Stock Report')

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

        headers = ['PCode', 'Batch code', 'Product Name', 'Stock', 'UoM', 'Purchase Rate', 'Stock Value', 'Stock Details']
        for col, header in enumerate(headers):
            sheet.write(1, col, header, header_format)

        domain = [('create_date', '<=', end_date), ('is_storable', '=', True)]
        products = self.env['product.product'].search(domain)
        row = 2
        company = self.env.company
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        sheet.merge_range('A1:H1', f"Warehouse : {warehouse.name if warehouse else ''}", header_format)
        total_stock = 0
        total_stock_value = 0
        i = 0
        for product in products:
            lots = self.env['stock.lot'].search([('product_id', '=', product.id), ('create_date', '<=', end_date)])
            if lots:
                stock_valuation_layers = self.env['stock.valuation.layer'].search([('product_id', '=', product.id), ('create_date', '<=', end_date), ('lot_id', 'in', lots.ids)])
                for lot in lots:
                    stock_qty = product.with_context(to_date=end_date, lot_id=lot.id, warehouse=warehouse.id).qty_available
                    stock_value = sum(stock_valuation_layers.filtered(lambda x: x.lot_id == lot).mapped('value')) if stock_valuation_layers else 0.0
                    stock_details = f'{stock_qty} {product.uom_id.name}'
                    total_stock += stock_qty
                    total_stock_value += stock_value
                    sheet.write(row, 0, product.default_code or '', cell_format)
                    sheet.write(row, 1, lot.name or '', cell_format)
                    sheet.write(row, 2, product.name or '', cell_format)
                    sheet.write(row, 3, stock_qty, number_format)
                    sheet.write(row, 4, product.uom_id.name if product.uom_id else '', cell_format)
                    sheet.write(row, 5, lot.standard_price, number_format)
                    sheet.write(row, 6, stock_value, number_format)
                    sheet.write(row, 7, stock_details, cell_format)
                    row += 1
            else:
                stock_valuation_layers = self.env['stock.valuation.layer'].search([('product_id', '=', product.id), ('create_date', '<=', end_date)])
                stock_value = sum(stock_valuation_layers.mapped('value')) if stock_valuation_layers else 0.0
                stock_qty = product.with_context(to_date=end_date).qty_available
                stock_details = f'{stock_qty} {product.uom_id.name}'
                total_stock += stock_qty
                total_stock_value += stock_value
                sheet.write(row, 0, product.default_code or '', cell_format)
                sheet.write(row, 1, '', cell_format)
                sheet.write(row, 2, product.name or '', cell_format)
                sheet.write(row, 3, stock_qty, number_format)
                sheet.write(row, 4, product.uom_id.name if product.uom_id else '', cell_format)
                sheet.write(row, 5, product.standard_price, number_format)
                sheet.write(row, 6, stock_value, number_format)
                sheet.write(row, 7, stock_details, cell_format)
                row += 1
        sheet.write(row, 3, total_stock, number_format)
        sheet.write(row, 6, total_stock_value, number_format)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 10)
        sheet.set_column(4, 4, 10)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 25)