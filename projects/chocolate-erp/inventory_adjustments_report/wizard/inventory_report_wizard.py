from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, time


class InventoryReportWizard(models.TransientModel):
    _name = 'inventory.report.wizard'
    _description = 'Inventory Report Wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string="Date To")
    stock_location_id = fields.Many2one('stock.location', string='Location')

    def generate_excel_report(self):
        if self.date_from > self.date_to:
            raise UserError(_("Date From must be less than or equal to Date To"))
        start_datetime = datetime.combine(self.date_from, time.min)
        end_datetime = datetime.combine(self.date_to, time.max)

        data = {
            'date_from': start_datetime,
            'date_to': end_datetime,
            'stock_location_id': self.stock_location_id.id,
            'location_name': self.stock_location_id.name
        }
        return self.env.ref('inventory_adjustments_report.action_inventory_report').report_action(self, data=data)
   