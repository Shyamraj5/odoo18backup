from odoo import models, api

class PosSalesReport(models.AbstractModel):
    _inherit= "report.point_of_sale.report_saledetails"
    _description= "POS Sales Report Total Amount Computation"

    @api.model
    def _get_taxes_info(self, taxes):
        total_tax_amount = 0
        total_base_amount = 0

        tax_list = list(taxes.values())

        for tax in tax_list:
            total_tax_amount += tax['tax_amount']

        for i in range(0, len(tax_list), 2):
            total_base_amount += tax_list[i]['base_amount']

        return {'tax_amount': total_tax_amount, 'base_amount': total_base_amount}