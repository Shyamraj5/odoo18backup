from odoo import models
import xlsxwriter
from datetime import datetime

class ScrapLossReport(models.AbstractModel):
    _name = 'report.code_ox_scrap_loss_report.scrap_loss_report'
    _description = 'Scrap Loss Excel Report'
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        start_date = datetime.strptime(data.get('start_date'), "%Y-%m-%d").date()
        end_date = datetime.strptime(data.get('end_date'), "%Y-%m-%d").date()
        current_date = datetime.now().date()

        # Separate domains for to-be-expired and expired
        domain_to_be_expired = [
            ('date_done', '>=', start_date), 
            ('date_done', '<=', end_date), 
            ('state', '=', 'done'),
            ('lot_id.expiration_date', '>', current_date)
        ]
        domain_expired = [
            ('date_done', '>=', start_date), 
            ('date_done', '<=', end_date), 
            ('state', '=', 'done'),
            ('lot_id.expiration_date', '<=', current_date)
        ]

        # Create formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#72BF78',
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        section_header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#ADD8E6',
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        date_format = workbook.add_format({
            'align': 'center',
            'border': 1
        })
        content_format = workbook.add_format({
            'align': 'center',
            'border': 1
        })
        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'center',
            'border': 1
        })
        total_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',
            'align': 'center',
            'border': 1,
            'bg_color': '#D3D3D3'
        })

        sheet = workbook.add_worksheet('Scrap Loss Stock Report')
        sheet.merge_range('A1:B1', 'Scrap Loss Stock Report', header_format)
        sheet.write('A2', 'As on Date', header_format)
        sheet.write('B2', str(current_date.strftime('%d/%m/%Y')), date_format)

        headers = [
            'Purchase Date', 'Product Code', 'Product', 'Posted Date',
            'Purchase Supplier', 'Purchase Quantity', 'Lot No',
            'Reason For Scrap / Loss', 'Scrap / Loss Quantity', 'UoM',
            'Unit Cost', 'Stock Value', 'Expiry Date', 'No of days left', 'Location'
        ]

        # Function to write report section
        def write_report_section(records, start_row, section_name):
            nonlocal sheet
            total_scrap_qty = 0
            total_stock_value = 0

            # Write section header
            sheet.merge_range(f'A{start_row+1}:O{start_row+1}', section_name, section_header_format)

            # Write headers
            for col_index, header in enumerate(headers):
                sheet.write(start_row+1, col_index, header, header_format)

            row_index = start_row + 2
            for scrap in records:
                lot = scrap.lot_id
                purchase_date = lot.purchase_order_ids[0].date_approve.strftime('%d/%m/%Y') if lot and lot.purchase_order_ids else ''
                product_code = scrap.product_id.default_code
                product_name = scrap.product_id.name
                posted_date = scrap.date_done.strftime('%d/%m/%Y')
                supplier = lot.purchase_order_ids[0].partner_id.name if lot and lot.purchase_order_ids else ''
                
                purchase_quantity = 0
                if lot and lot.purchase_order_ids:
                    for po in lot.purchase_order_ids:
                        purchase_quantity += sum(
                            line.qty_received
                            for line in po.order_line.filtered(lambda l: l.product_id == lot.product_id)
                        )
                
                lot_no = lot.name if lot else ''
                reason = ','.join([reason.name for reason in scrap.scrap_reason_tag_ids])
                scrap_qty = scrap.scrap_qty
                uom = scrap.product_uom_id.name
                unit_cost = scrap.product_id.standard_price
                stock_value = unit_cost * scrap_qty
                expiry_date = lot.expiration_date.strftime('%d/%m/%Y') if lot and lot.expiration_date else ''
                no_of_days_left = (lot.expiration_date.date() - current_date).days if lot and lot.expiration_date else ''
                location = scrap.location_id.name
                
                total_scrap_qty += scrap_qty
                total_stock_value += stock_value
                
                values = [
                    purchase_date, product_code, product_name, posted_date,
                    supplier, purchase_quantity, lot_no, reason, scrap_qty, uom,
                    unit_cost, stock_value, expiry_date, no_of_days_left, location
                ]

                for col_index, value in enumerate(values):
                    if isinstance(value, (float, int)):
                        sheet.write(row_index, col_index, value, number_format)
                    else:
                        sheet.write(row_index, col_index, str(value), content_format)

                row_index += 1

            # Write total row
            sheet.write(row_index, 7, 'Total', total_format)
            sheet.write(row_index, 8, total_scrap_qty, total_format)
            sheet.write(row_index, 11, total_stock_value, total_format)

            return row_index

        # Fetch and write To Be Expired section
        to_be_expired_records = self.env['stock.scrap'].search(domain_to_be_expired)
        last_row = write_report_section(to_be_expired_records, 3, 'To Be Expired')

        # Leave a blank row and then write Expired section
        expired_records = self.env['stock.scrap'].search(domain_expired)
        write_report_section(expired_records, last_row + 2, 'Expired')

        # Adjust column widths
        for col_index in range(len(headers)):
            sheet.set_column(col_index, col_index, 20)