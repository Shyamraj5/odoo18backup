from odoo import models, fields, api, _
from datetime import date, timedelta
import time


class LocationReportWizard(models.TransientModel):
    _name = 'location.report.wizard'
    _description = 'Location Report Wizard'

    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))
    period_lenght = fields.Integer(string='Period Length (days)', default=10)
    target_move = fields.Selection(
        [('posted', 'Posted Entries'), ('all', 'All Entries')], 
        string='Target Moves', default='posted'
    )
    route_location = fields.Many2many(
        'route.route', 
        string='Route Locations'
    )

    def generate_excel_report(self):
        data = {
            'date_from': self.date_from,
            'period_lenght': self.period_lenght,
            'target_move': self.target_move,
            'route_location_ids': self.route_location.ids,
        }
        return self.env.ref('location_report.action_location_report').report_action(self, data=data)
