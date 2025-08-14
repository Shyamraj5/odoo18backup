from odoo import models
import xlsxwriter

class StockInOutReport(models.AbstractModel):
    _name = 'report.inventory_stock_report.stock_in_out_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        report_data = data.get('report_data', [])
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 14,
            'border': 1
        })
        
        column_header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
            'bg_color': '#D3D3D3'
        })
        
        date_format = workbook.add_format({
           
            'border': 1
        })
        
        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1
        })
        
        text_format = workbook.add_format({
            'border': 1
        })

        worksheet = workbook.add_worksheet('Stock In Out Report')
        
        worksheet.set_column('A:A', 12)  
        worksheet.set_column('B:B', 15)  
        worksheet.set_column('C:C', 30)  
        worksheet.set_column('D:D', 15)  
        worksheet.set_column('E:E', 15)  
        worksheet.set_column('F:H', 12) 

  
        worksheet.merge_range('A1:H1', 'Stock In Out Report', header_format)
        
        

        headers = ['Date', 'Voucher Type', 'Particulars', 'Ref No', 
                  'BarCode', 'In', 'Out', 'Balance']
        worksheet.write_row('A4', headers, column_header_format)


        row = 4
        for record in report_data:
            worksheet.write(row, 0, record['date'], date_format)
            worksheet.write(row, 1, record['picking_type_id'], text_format)
            worksheet.write(row, 2, record['partner_name'] or '', text_format)
            worksheet.write(row, 3, record['ref_no'] or '', text_format)
            worksheet.write(row, 4, record['batch_code'] or '', text_format)
            worksheet.write(row, 5, record['in_qty'] or 0, number_format)
            worksheet.write(row, 6, record['out_qty'] or 0, number_format)
            worksheet.write(row, 7, record['balance'], number_format)
            row += 1
