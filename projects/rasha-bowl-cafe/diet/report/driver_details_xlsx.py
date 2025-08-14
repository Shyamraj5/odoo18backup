from odoo import models


class CustomerDailyReport(models.AbstractModel):
    _name = "report.driver_details_report_xlsx"
    _description = "Report for driver details"
    _inherit = "report.report_xlsx.abstract"


    def generate_xlsx_report(self, workbook, data, lines):
        format1a =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "bold": True,
                    "valign": "vcenter",
                    "bg_color": "#b7dfa9"

            }
        )
        format1b =workbook.add_format(
            {
                "font_size": 20,
                "bottom" : True,
                "right" : True,
                "left": True,
                "top": True,
                "align": "center",
                "bold": True,
                "bg_color" :"#8bc388",
                "font_color" : "white",
                "valign": "vcenter"
            }
        )
        format1c =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "align": "center",
                "valign": "vcenter",
                "num_format": "#,##0.00",
                })
        
        format1d =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "bold": True,
                    "valign": "vcenter",
                    "bg_color": "#8bc388"

            }
        )
        format1e =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "align": "left",
                "valign": "vcenter",
                "num_format": "#,##0.00",
                })
        

        worksheet = workbook.add_worksheet("DRIVER DETAILS REPORT")
        worksheet.merge_range("A1:F1", "FEED", format1b)
        worksheet.merge_range("A2:F2", "DRIVER DETAILS REPORT", format1d)
        worksheet.set_row(0, 50)
        worksheet.set_row(1, 30)
        worksheet.set_row(2, 20)
        worksheet.set_column("A:A", 5)
        worksheet.set_column("B:B", 10)
        worksheet.set_column("C:C", 30)
        worksheet.set_column("D:D", 15)
        worksheet.set_column("E:E", 40)
        worksheet.set_column("F:F", 40)
        worksheet.write("A3", "SI NO", format1a)
        worksheet.write("B3", "DRIVER ID",format1a)
        worksheet.write("C3", "DRIVER",format1a)
        worksheet.write("D3", "MOBILE",format1a)
        worksheet.write("E3", "AREA",format1a)

        
        driver_records = self.env['area.driver'].search([])

        row = 4
        i = 0
        for driver in driver_records:
            i += 1
            length = len(driver.service_area_ids)
            if length > 1 :
                worksheet.merge_range("A%s:A%s" % (row,row +length -1), str(int(i)), format1c)
                worksheet.merge_range("B%s:B%s" % (row,row +length -1), driver.code, format1c)
                worksheet.merge_range("C%s:C%s" % (row,row +length -1), driver.name, format1c)
                worksheet.merge_range("D%s:D%s" % (row,row +length -1), driver.phone, format1c)
                for area in driver.service_area_ids:
                    worksheet.write("E%s" % row, area.name, format1e)
                    row +=1
                row+=1
            else:
                worksheet.write("A%s" % row, str(int(i)), format1c)
                worksheet.write("B%s" % row, driver.code, format1c)
                worksheet.write("C%s" % row, driver.name, format1c)
                worksheet.write("D%s" % row, driver.phone, format1c)
                for area in driver.service_area_ids:
                    worksheet.write("E%s" % row, area.name, format1e)
                    row += 1
                row+=1
        
            
           