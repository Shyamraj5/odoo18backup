from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
from calendar import monthrange

class SalesTargetWizard(models.TransientModel):
    _name = 'sales.target.wizard'
    _description = 'Incentive Report Wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string="Date To", default=lambda *a: time.strftime('%Y-%m-%d'))

    def generate_excel_report(self):
        if self.date_from > self.date_to:
            raise UserError(_("Date From must be less than or equal to Date To"))

        if self.date_from.month != self.date_to.month or self.date_from.year != self.date_to.year:
            raise UserError(_("The selected dates must belong to the same month"))

        if self.date_from.day != 1:
            raise UserError(_("Date From must be the first day of the month"))

        last_day_of_month = monthrange(self.date_to.year, self.date_to.month)[1]
        if self.date_to.day != last_day_of_month:
            raise UserError(_("Date To must be the last day of the month"))

        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('sales_excel_report.sales_target_report_action').report_action(self, data=data)
