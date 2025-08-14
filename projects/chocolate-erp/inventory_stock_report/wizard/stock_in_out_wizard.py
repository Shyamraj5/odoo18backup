from collections import defaultdict
from odoo import models, fields
from datetime import date, timedelta

class WeeklySalesWizard(models.TransientModel):
    _name = 'stock.in.out.wizard'
    _description = 'Inventory Stock Report'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    
    product_ids = fields.Many2many('product.product', string="Products")
    lot_ids = fields.Many2many('stock.lot', string="Lots")

    def generate_report(self):
        StockMoveLine = self.env['stock.move.line']
        lots = self.env['stock.lot'].search([])
        def get_movement_data():
            domain = [('state', '=', 'done')]
            
            if self.start_date and self.end_date:
                domain.append(('date', '>=', self.start_date))
                domain.append(('date', '<=', self.end_date))
            
            if self.product_ids:
                domain.append(('product_id', 'in', self.product_ids.ids))
                
            if self.lot_ids:
                domain.append(('lot_id', 'in', self.lot_ids.ids))

            move_lines = StockMoveLine.search(domain)
            move_lines = move_lines.sorted(key=lambda r: r.lot_id)
            
            report_data = []
            balance = 0
            
            for move_line in move_lines:
                batch_code = move_line.lot_id.name if move_line.lot_id else ''
                product_name = move_line.product_id.name
                
                picking_type = move_line.move_id.picking_type_id.code
                in_qty = move_line.quantity if picking_type == 'incoming' else 0
                out_qty = move_line.quantity if picking_type == 'outgoing' else 0
                
                balance += in_qty - out_qty
                
                report_data.append({
                    'date': move_line.date,
                    'picking_type_id': move_line.move_id.picking_type_id.name,
                    'partner_name': move_line.move_id.partner_id.name or '',
                    'ref_no': move_line.move_id.origin or '',
                    'batch_code': batch_code,
                    'in_qty': in_qty,
                    'out_qty': out_qty,
                    'balance': balance,
                    'product_name': product_name,
                    'lot_name': batch_code,
                    'uom': move_line.product_uom_id.name
                })
            
            return report_data
        
        report_data = get_movement_data()
        
        return self.env.ref('inventory_stock_report.stock_in_out_report').report_action(
            self,
            data={'report_data': report_data}
        )