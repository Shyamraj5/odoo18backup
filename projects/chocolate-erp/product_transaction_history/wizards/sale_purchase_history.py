from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SalePurchseHistoryWizard(models.TransientModel):
    _name = "sale.purchase.history.wizard"
    _description = "History of Sale and Purchase of Product"


    product_id = fields.Many2one('product.product',string="Product")
    partner_id = fields.Many2one('res.partner', string="Customer")
    history_type = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchase'),
        ('invoice', 'Invoice')
    ], string='History of', required=True, default='sale')
    history_line_ids = fields.One2many(
        'product.history.line', 
        'wizard_id', 
        string='History Lines'
    )

    @api.onchange('history_type')
    def onchange_history_type(self):
        self.view_history()

    def view_history(self):
        self.ensure_one()
        
        self.history_line_ids = [(5, 0, 0)]
        
        history_lines = []
        
        if self.history_type == 'sale':
            sale_lines = self.env['sale.order.line'].search([
                ('product_id', '=', self.product_id.id),
                ('order_id.partner_id', '=', self.partner_id.id),
                ('order_id.state', '=', 'sale')
            ], order='create_date desc')
            
            for line in sale_lines:
                history_lines.append((0, 0, {
                    'date': line.create_date,
                    'partner_id': line.order_id.partner_id.id,
                    'quantity': line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'received': line.qty_delivered,
                    'billed': line.price_total,
                    'total_price' : line.price_subtotal,
                    'order' : line.order_id.name,
                    'wizard_id': self.id
                }))
        
        elif self.history_type == 'purchase':
            purchase_lines = self.env['purchase.order.line'].search([
                ('product_id', '=', self.product_id.id),
                ('order_id.state', 'in', ['purchase','done'])
            ],order='create_date desc')
            
            for line in purchase_lines:
                history_lines.append((0, 0, {
                    'date': line.create_date,
                    'partner_id': line.order_id.partner_id.id,
                    'quantity': line.product_qty,
                    'price_unit': line.price_unit,
                    'received' : line.qty_received,
                    'billed' : line.qty_invoiced,
                    'total_price' : line.price_subtotal,
                    'order' : line.order_id.name,
                    'wizard_id': self.id
                }))
        
        elif self.history_type == 'invoice':
            invoice_lines = self.env['account.move.line'].search([
                ('product_id', '=', self.product_id.id),
                ('move_id.partner_id', '=', self.partner_id.id)
              ], order='create_date desc')
            
            for line in invoice_lines:
                history_lines.append((0, 0, {
                    'date': line.create_date,
                    'partner_id': line.move_id.partner_id.id,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'total_price' : line.price_subtotal,
                    'order' : line.move_id.name,
                    'wizard_id': self.id
                }))
        
        self.history_line_ids = history_lines
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.purchase.history.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }


class ProductHistoryLine(models.TransientModel):
    _name = 'product.history.line'
    _description = 'Product History Line'

    wizard_id = fields.Many2one('sale.purchase.history.wizard', string='Wizard')
    order = fields.Char(string="Order")
    date = fields.Datetime(string='Date')
    partner_id = fields.Many2one('res.partner', string='Partner')
    quantity = fields.Float(string='Quantity')
    received = fields.Float(string='Received')
    billed = fields.Float(string='Billed')
    price_unit = fields.Float(string='Unit Price')
    total_price = fields.Float(string="Total Price")