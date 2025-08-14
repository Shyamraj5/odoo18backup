from odoo import models


class IndividualDriverExcelReport(models.AbstractModel):
    _name = "report.individual_driver_report_xlsx"
    _description = "Excel report of Individual Driver"
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
                    "bg_color" :"#8bc388",}
        )
        format1b =workbook.add_format(
            {
                "font_size": 11,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "num_format": "#,##0.00",
                })
        format1c =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "bold": True,
                    "valign": "vcenter",
                    }
        )
        format1d =workbook.add_format(
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
        format1e =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "right",
                    "bold": True,
                    "valign": "vcenter"
                    }
        )
        format1f =workbook.add_format(
            {
                    "font_size": 11,
                    "bottom": True,
                    "right": True,
                    "left": True,
                    "top": True,
                    "align": "center",
                    "valign": "vcenter",
                    }
        )
        worksheet = workbook.add_worksheet("DRIVER")
        worksheet.merge_range(
            "A1:B1", "FEED", format1d)
        
        if lines.phone:
            worksheet.merge_range(
                "A2:B2", lines.code + "                                                PHONE: "+ lines.phone, format1a)
        else:
            worksheet.merge_range(
                "A2:B2", lines.code, format1a)
        
        worksheet.merge_range(
                "A3:B3", "DRIVER: "+lines.name.upper(), format1a)
        worksheet.set_row(0, 30)
        worksheet.set_row(1, 30)
        worksheet.set_row(2, 30)
        worksheet.set_column("A:A", 7)
        worksheet.set_column("B:B", 60)
        worksheet.write("A4","NO", format1c)
        worksheet.write("B4","AREA", format1c)
        
        row = 5
        i = 0
        for area in lines.service_area_ids:
            i += 1
            worksheet.write("A%s" %row,str(int(i)), format1f)
            worksheet.write("B%s" %row,area.name, format1b)
            row += 1

        worksheet.merge_range("A%s:B%s" %(row,row),"TOTAL: "+str(len(lines.service_area_ids)), format1e)


       