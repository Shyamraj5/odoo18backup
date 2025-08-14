from odoo import models, fields, api, _
from datetime import date, timedelta
import time


class SalesmanAgeingReportWizard(models.TransientModel):
    _name = 'salesman.ageing.report.wizard'
    _description = 'Salesman Ageing Report Wizard'

    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))
    period_lenght = fields.Integer(string='Period Length (days)', default=10)
    target_move = fields.Selection([('posted', 'Posted Entries'),
                                    ('all', 'All Entries')], 
                                    string='Target Moves',default='posted')
    customer_ids = fields.Many2many('res.partner', string='Customers')
    salesman_ids = fields.Many2many('res.users', string='Salesmans',
                                    domain=lambda self: [("groups_id", "=", self.env.ref("sales_team.group_sale_salesman").id)])

    def generate_excel_report(self):
        data = {
            'date_from': self.date_from,
            'period_lenght': self.period_lenght,
            'target_move': self.target_move,
            'salesman_ids': self.salesman_ids.ids,
        }
        return self.env.ref('salesman_ageing_report.action_salesman_ageing_report').report_action(self, data=data)