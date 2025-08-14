from odoo import models, fields

class PackageReportWizard(models.Model):
    _name = 'package.report.wizard'
    _description = 'Package Report Wizard'
    
    def view_package_report(self):
        return self.env.ref("diet.action_package_report").report_action(self,config=False)
                                                                        

    def export_package_report(self):
        return self.env.ref("diet.action_report_package_report_xlsx").report_action(self,config=False)

    