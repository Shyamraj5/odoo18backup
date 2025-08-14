from odoo import models
from io import BytesIO
import xlsxwriter

class SalesExcelReport(models.AbstractModel):
    _name = 'report.sales_excel_report.sales_report'
    _description = 'Sales Excel Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        product_ids = data.get('product_ids')
        customer_ids = data.get('customer_ids')
        location_ids = data.get('location_ids')
        company_ids = data.get('company_ids')

        domain = []
        if start_date:
            domain.append(('date_order', '>=', start_date))
        if end_date:
            domain.append(('date_order', '<=', end_date))
        if product_ids:
            domain.append(('order_line.product_id', 'in', product_ids))
        if customer_ids:
            domain.append(('partner_id', 'in', customer_ids))
        if location_ids:
            domain.append(('order_line.move_ids.location_id', 'in', location_ids))
        if company_ids:
            domain.append(('company_id', 'in', company_ids))

        sales_orders = self.env['sale.order'].search(domain)

        worksheet = workbook.add_worksheet('Sales Report')

        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D9E1F2'
        })

        cell_format_left = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })

        cell_format_right = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter'
        })

        company_name_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#F4CCCC',
            'size': 14
        })

        show_quantity_unit_price = bool(product_ids)

        headers = ['Date', 'Sale Order Number', 'Customer', 'Invoice Status', 'Total']
        if show_quantity_unit_price:
            headers.insert(4, 'Quantity')
            headers.insert(5, 'Unit Price')

        total_col_idx = len(headers) - 1

        company_name = self.env['res.company'].browse(company_ids[0]).name if company_ids else self.env.user.company_id.name
        worksheet.merge_range(0, 0, 0, total_col_idx, company_name, company_name_format)

        filter_info = []
        if product_ids:
            product_names = ', '.join(self.env['product.product'].browse(product_ids).mapped('name'))
            filter_info.append(f"Products: {product_names}")

        if location_ids:
            warehouse_names = ', '.join(self.env['stock.location'].browse(location_ids).mapped('name'))
            filter_info.append(f"Warehouse: {warehouse_names}")

        filter_text = ' | '.join(filter_info) if filter_info else "No filters applied"
        worksheet.merge_range(1, 0, 1, total_col_idx, filter_text, cell_format_left)

        for col_num, header in enumerate(headers):
            worksheet.write(2, col_num, header, header_format)

        row = 3
        grand_total = 0
        for order in sales_orders:
            total_quantity = sum(line.product_uom_qty for line in order.order_line)
            total_sales_amount = sum(line.price_subtotal for line in order.order_line)

            unit_price = (
                sum(line.price_unit * line.product_uom_qty for line in order.order_line) / total_quantity
                if total_quantity else 0
            )
            invoice_names = ', '.join(order.invoice_ids.mapped('name')) if order.invoice_ids else 'No Invoice'

            worksheet.write(row, 0, order.date_order.strftime('%Y-%m-%d'), cell_format_left)
            worksheet.write(row, 1, order.name, cell_format_left)
            worksheet.write(row, 2, order.partner_id.name or 'Unknown Customer', cell_format_left)
            worksheet.write(row, 3, invoice_names, cell_format_left)

            if show_quantity_unit_price:
                worksheet.write(row, 4, round(total_quantity, 2), cell_format_right)
                worksheet.write(row, 5, round(unit_price, 2), cell_format_right)

            worksheet.write(row, total_col_idx, round(total_sales_amount, 2), cell_format_right)
            grand_total += total_sales_amount
            row += 1

        grand_total_label_col = 3 if not show_quantity_unit_price else 5
        worksheet.write(row, grand_total_label_col, 'Grand Total', header_format)
        worksheet.write(row, total_col_idx, round(grand_total, 2), cell_format_right)

        worksheet.set_column(0, 0, 12)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 3, 25)
        if show_quantity_unit_price:
            worksheet.set_column(4, 4, 10)
            worksheet.set_column(5, 5, 12)
        worksheet.set_column(total_col_idx, total_col_idx, 15)
