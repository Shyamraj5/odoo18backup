from odoo import models, fields, api, _

class StockAgeingReportWizard(models.TransientModel):
    _name = 'stock.ageing.report.wizard'
    _description = 'Stock Ageing Report Wizard'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    product_id = fields.Many2one('product.product', string='Product')
    date = fields.Date(string='Date', default=fields.Date.today)

    def print_report(self):
        data = {
            'warehouse_id': self.warehouse_id.id,
            'product_id': self.product_id.id,
            'date': self.date,
        }
        return self.env.ref('code_ox_stock_ageing_report.action_report_stock_ageing').report_action(self, data=data)