from odoo import models, fields
from datetime import date, timedelta

class ScrapLossWizard(models.TransientModel):
    _name = 'scrap.loss.wizard'
    _description = 'Scrap Loss Wizard'

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
        return self.env.ref('code_ox_scrap_loss_report.action_scrap_loss_report').report_action(self, data=data)