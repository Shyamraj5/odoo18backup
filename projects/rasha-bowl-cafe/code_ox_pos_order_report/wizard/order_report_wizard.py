from odoo import models, fields, api, _
from datetime import date, timedelta
import time
from odoo.exceptions import UserError


class PosOrderReportWizard(models.TransientModel):
    _name = 'pos.order.report.wizard'
    _description = 'Pos Order Report Wizard'
 
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string="To Date", default=lambda *a: time.strftime('%Y-%m-%d'))
    customer_type = fields.Selection([('walk_in_customer', 'Walk in Customer'), ('hotel_customer', 'Hotel Customer'), 
                                      ('complementary_customer', 'Complementary Customer')], default=None)
    partner_ids = fields.Many2many('res.partner', string="Customer")
    order_type_ids = fields.Many2many('pos.order.type', string="Order Type")

    def generate_excel_report(self):
        if self.date_from > self.date_to:
            raise UserError(_("To Date must be greater than From Date"))
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'customer_type': self.customer_type,
            'partner_ids': self.partner_ids.ids if self.partner_ids else False,
            'order_type_ids': self.order_type_ids.ids if self.order_type_ids.ids else False
        }
        return self.env.ref('code_ox_pos_order_report.action_xml_order_report').report_action(self, data=data)

    def generate_pdf_report(self):
        if self.date_from > self.date_to:
            raise UserError(_("To Date must be greater than From Date"))
        data ={
            'date_from': self.date_from,
            'date_to': self.date_to,
            'customer_type': self.customer_type,
            'partner_ids': self.partner_ids.ids if self.partner_ids else False,
            'order_type_ids': self.order_type_ids.ids if self.order_type_ids.ids else False
        }
        return self.env.ref('code_ox_pos_order_report.action_pdf_order_report').report_action(self, data=data)
        