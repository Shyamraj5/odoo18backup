from odoo import models, fields, api
from datetime import datetime


class VatReportWizard(models.TransientModel):
    _name = 'vat.report.wizard'
    _description = "Daily Vat Report Wizard"
    
    months = fields.Selection(
        [
            ('01', 'January'), ('02', 'February'), ('03', 'March'),
            ('04', 'April'), ('05', 'May'), ('06', 'June'),
            ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
        string='Month',
        required=True
    )
    years = fields.Selection(
        [(str(num), str(num)) for num in range(2020, 2031)],
        string='Year',
        default=str(fields.Date.today().year),
        required=True
    )
    
    def action_vat_report(self):
        data = {'months': self.months,
                'years':self.years}
        return self.env.ref('codeox_vat_report.action_print_html_report').report_action(self, data=data)
    
    
    
