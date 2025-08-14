from odoo import models
from datetime import datetime, timedelta

class PackageReportExcel(models.AbstractModel):
    _name = "report.diet.package_report_excel"
    _description = "Package Report Excel"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, lines):
        format1b =workbook.add_format(
            {
                "font_size": 20,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "align": "center",
                "bold":True
            })
        
        
        format2b =workbook.add_format(
            {
                "font_size": 20,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "align":"center",
                })
        
        format3b =workbook.add_format(
            {
                "font_size": 20,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "align":"right",              
                
            })
        
        format4b =workbook.add_format(
            {
                "font_size": 20,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "align":"left",              
                
            })
        
        format5b =workbook.add_format(
            {
                "font_size": 25,
                "bottom": True,
                "right": True,
                "left": True,
                "top": True,
                "valign": "vcenter",
                "align": "center",
                "bold":True,
                "font_color":"#ffffff",               
                "bg_color": "#eb3489",
            })
        
        worksheet = workbook.add_worksheet("Package Report")
        worksheet.set_row(0, 50)
        worksheet.set_column("A:A", 10)
        worksheet.set_column("B:B", 55)
        worksheet.set_column("C:C", 30)
        worksheet.set_column("D:D", 25)
        worksheet.merge_range("A1:D1", "PACKAGE REPORT",format5b)
        worksheet.write("A2", "Sl. No.",format1b)
        worksheet.write("B2", "Plan Name",format1b)
        worksheet.write("C2", "Total Subscribers",format1b)
        worksheet.write("D2", "Total Amount",format1b)
        row = 3
        plan_ids = self.env['subscription.package.plan'].search([])
        report_data = []
        for plan in plan_ids:
            total_customers = 0
            total_amount = 0
            subscriptions = self.env['diet.subscription.order'].search([
                ('plan_id', '=', plan.id),
                ('state', 'in', ["paid","in_progress"])
            ])
            total_customers = len(subscriptions.mapped('partner_id'))
            total_amount = sum(subscriptions.mapped('grand_total'))
            report_data.append({
                'plan': plan.name,
                'subscribers': total_customers,
                'amount': round(total_amount,2)
            })
        sl_no = 1
        for data in report_data:
            worksheet.write("A%s" %row, sl_no,format2b )
            worksheet.write("B%s" %row, data['plan'],format4b )
            worksheet.write("C%s" %row, data['subscribers'],format2b )
            worksheet.write("D%s" %row, data['amount'],format3b )
            sl_no += 1
            row += 1