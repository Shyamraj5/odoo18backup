from . import sale_order

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_print_proforma_delivery(self):
        """Action to print proforma delivery report"""
        return self.env.ref('proforma_delivery_slip.action_report_proforma_delivery').report_action(self)
