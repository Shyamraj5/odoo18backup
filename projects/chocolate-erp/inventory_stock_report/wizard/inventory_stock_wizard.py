from odoo import models, fields
from datetime import date, timedelta

class WeeklySalesWizard(models.TransientModel):
    _name = 'inventory.stock.wizard'
    _description = 'Inventory Stock Report'

    end_date = fields.Datetime(
        string="Inventory at Date",
        default=fields.Datetime.now
    )

    def generate_excel_report(self):
        data = {
            'end_date': self.end_date,
        }
        return self.env.ref('inventory_stock_report.action_inventory_stock_report').report_action(self, data=data)