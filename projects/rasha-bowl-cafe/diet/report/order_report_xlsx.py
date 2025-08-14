from odoo import models

class Order_report(models.AbstractModel):
    _name = "report.diet.order_report_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Order Report XLSX"

    def generate_xlsx_report(self, workbook, data, lines):
        # Set up the worksheet
        sheet = workbook.add_worksheet('Order Report')
        letters = []
        letters_max_len = 40
        for i in range(65, 91):  # A to Z
            letters.append(chr(i))
        for i in range(65, 91):  # AA to ZZ
            for j in range(65, 91):
                if len(letters) == letters_max_len:
                    break
                letters.append(chr(i) + chr(j))

        # Define formats
        header_format = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True,'border': 1
        })
        dislike_format = workbook.add_format({
            'font_color': '#FF0000', 'valign': 'vcenter', 'text_wrap': True, 'align': 'center','border': 1
        })
        normal_format = workbook.add_format({
            'valign': 'vcenter', 'text_wrap': True, 'align': 'center','border': 1
        })
        
        # New format for rows with sl_no (grey background)
        sl_no_format = workbook.add_format({
            'bg_color': '#D3D3D3', 'valign': 'vcenter', 'text_wrap': True, 'border': 1, 'bold': True, 'align': 'center','border': 1
        })

        # Set column widths
        sheet.set_column('A:A', 6)   # Sl No
        sheet.set_column('B:B', 50)  # Meal Name
        sheet.set_column('C:J', 15)  # PC Combinations and Totals

        # Start writing the report
        sheet.set_row(0, 40)
        row = 1
        sheet.merge_range(f'A{row}:O{row}', 'Order Report', workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        }))
        row += 2

        # Loop through meal categories
        for meal_category, meals in data['report_data'].items():
            row += 1
            sheet.merge_range(f'A{row}:O{row}', meal_category, header_format)
            sheet.set_row(row, 30)
            row += 1
            sheet.write(f'A{row}', 'Sl No', header_format)
            sheet.write(f'B{row}', 'Meal Name', header_format)
            col = 1
            for pc_combination in data['pc_combinations']:
                col += 1
                sheet.write(f'{letters[col]}{row}', pc_combination, header_format)
            sheet.write(f'{letters[col + 1]}{row}', 'No Of Meals', header_format)
            sheet.write(f'{letters[col + 2]}{row}', 'Total', header_format)

            # Write each meal data
            for meal_data in meals:
                sheet.set_row(row, 25)
                row += 1
                
                # Use sl_no_format if sl_no is present, otherwise use normal_format
                row_format = sl_no_format if meal_data.get('sl_no') else normal_format
                dislike_color_format = dislike_format if meal_data.get('is_dislike', False) else row_format
                
                # Write sl_no, meal name, and rest of the row with appropriate format
                sheet.write(f'A{row}', meal_data.get('sl_no', ''), row_format)  # Write sl_no with grey background if present
                sheet.write(f'B{row}', meal_data['meal_name'], dislike_color_format)
                
                col = 1
                total_grams = 0
                for pc_combination in data['pc_combinations']:
                    protein = int(pc_combination.split('/')[0][1:])
                    col += 1
                    pc_count = meal_data.get(pc_combination, 0)  # Handle cases where the PC combination might not exist
                    sheet.write(f'{letters[col]}{row}', pc_count, row_format)  # Center and apply the same format as before
                    total_grams += (protein / 100) * pc_count

                # Write sub_total and total grams with the same centered format
                sheet.write(f'{letters[col + 1]}{row}', meal_data['sub_total'], row_format)  # No of Meals centered
                sheet.write(f'{letters[col + 2]}{row}', total_grams, row_format)  # Total centered
            row += 1
