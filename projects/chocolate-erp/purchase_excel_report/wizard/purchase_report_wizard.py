from odoo import models, fields, api, _
from datetime import date, timedelta
import time


class PurchaseReportWizard(models.TransientModel):
    _name = 'purchase.report.wizard'
    _description = 'Purchase Report Wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string="Date To", default=lambda *a: time.strftime('%Y-%m-%d'))

    def generate_excel_report(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('purchase_excel_report.action_purchase_report').report_action(self, data=data)
    