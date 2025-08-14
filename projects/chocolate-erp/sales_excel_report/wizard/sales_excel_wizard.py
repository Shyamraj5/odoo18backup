from odoo import models, fields

class SalesExcelWizard(models.TransientModel):
    _name = 'sales.excel.wizard'
    _description = 'Sales Excel Wizard'

    start_date = fields.Date(string='From Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='To Date', required=True, default=fields.Date.context_today)
    product_id = fields.Many2many('product.product', string='Products')
    customer_id = fields.Many2many('res.partner', string='Customers')
    location_id = fields.Many2many('stock.location', string='Inventory Locations', domain=[('usage', '=', 'internal')])
    company_id = fields.Many2many('res.company', string='Companies')

    def generate_excel_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'product_ids': self.product_id.ids,
            'customer_ids': self.customer_id.ids,
            'location_ids': self.location_id.ids,
            'company_ids': self.company_id.ids,
        }
        return self.env.ref('sales_excel_report.action_sales_excel_report').report_action(self, data=data)
