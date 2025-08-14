from odoo import models, fields
from datetime import date, datetime, timedelta


class InventoryStockWizard(models.TransientModel):
    _name = 'inventory.stock.expiry.wizard'
    _description = 'Inventory Stock Report'

    as_on_date = fields.Date(
            string="Date",
            default=fields.Datetime.now
        )


    def generate_expiry_stock_report(self):

        to_be_expired_domain = [
            ('expiration_date', '>', self.as_on_date),
        ]

        expired_domain = [
            ('expiration_date', '<=', self.as_on_date),
        ]
        to_be_expired_lots = self.env['stock.lot'].search(to_be_expired_domain)
        expired_lots = self.env['stock.lot'].search(expired_domain)

        to_be_expired_data = []
        expired_data = []

        def process_lot_with_purchase_orders(lot):
            rows = []
            expiration_date = lot.expiration_date.date() if isinstance(lot.expiration_date, datetime) else lot.expiration_date
            days_left = (expiration_date - self.as_on_date).days
            if days_left < 0:
                days_left = abs(days_left)
                
            if lot.purchase_order_ids:
                for po in lot.purchase_order_ids[0]:
                    purchase_quantity = sum(
                        line.qty_received
                        for line in po.order_line.filtered(lambda l: l.product_id == lot.product_id)
                    )
                    vendor_name = po.partner_id.name if po.partner_id else ''  # Get vendor name
                    if lot.location_id:
                        rows.append({
                            'purchase_date': po.date_order.strftime('%d-%m-%Y'),
                            'product': lot.product_id.display_name,
                            'purchase_quantity': purchase_quantity,
                            'vendor':vendor_name,
                            'lot_no': lot.name,
                            'quantity': lot.product_qty,
                            'uom': lot.product_uom_id.name,
                            'stock_value': lot.total_value,
                            'cost':lot.avg_cost,
                            'expiry_date': lot.expiration_date.strftime('%d-%m-%Y'),
                            'days_left': days_left,
                            'location': lot.location_id.display_name,
                        })
                    else:
                        quant_ids = lot.quant_ids.filtered(lambda x: x.location_id.usage == 'internal')
                        for quant in quant_ids:
                            rows.append({
                            'purchase_date': po.date_order.strftime('%d-%m-%Y'),
                            'product': lot.product_id.display_name,
                            'purchase_quantity': purchase_quantity,
                            'vendor':vendor_name,
                            'lot_no': lot.name,
                            'quantity': quant.quantity,
                            'uom': lot.product_uom_id.name,
                            'stock_value': quant.value,
                            'cost':lot.avg_cost,
                            'expiry_date': lot.expiration_date.strftime('%d-%m-%Y'),
                            'days_left': days_left,
                            'location': quant.location_id.display_name,
                        })
            else:
                rows.append({
                    'purchase_date': '',
                    'product': lot.product_id.name,
                    'purchase_quantity': 0,
                    'lot_no': lot.name,
                    'quantity': lot.product_qty,
                    'uom': lot.product_uom_id.name,
                    'stock_value': lot.total_value,
                    'cost':lot.avg_cost,
                    'expiry_date': lot.expiration_date.strftime('%d-%m-%Y'),
                    'days_left': days_left,
                    'location': lot.location_id.display_name,
                })

            return rows

        for lot in to_be_expired_lots:
            to_be_expired_data.extend(process_lot_with_purchase_orders(lot))

        for lot in expired_lots:
            expired_data.extend(process_lot_with_purchase_orders(lot))

        to_be_expired_data.sort(key=lambda x: x['days_left'])
        expired_data.sort(key=lambda x: x['days_left'])

        return self.env.ref('inventory_stock_report.action_expiry_stock_report_xlsx').report_action(
            self, data={
                'to_be_expired': to_be_expired_data,
                'expired': expired_data,
                'as_on_date': self.as_on_date.strftime('%d-%m-%Y'),
            }
        )
