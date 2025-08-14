from odoo import models, fields
from datetime import date, timedelta

class WeeklySalesWizard(models.TransientModel):
    _name = 'weekly.sales.wizard'
    _description = 'Weekly Sales Wizard'

    start_date = fields.Date(
        string="Start Date", 
        required=True, 
        default=lambda self: (date.today() - timedelta(days=7))
    )
    end_date = fields.Date(
        string="End Date", 
        required=True, 
        default=lambda self: date.today()
    )

    def generate_excel_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return self.env.ref('weekly_sales_report.action_weekly_sales_report').report_action(self, data=data)