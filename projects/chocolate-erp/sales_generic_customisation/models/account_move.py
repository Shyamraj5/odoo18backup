from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = "account.move"

    sale_type = fields.Selection([
        ('wholesale', 'Wholesale'),
        ('b2b', 'B2B'),
        ('vansale', 'Van Sale')
    ], string="Sales Type")

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    lot_id = fields.Many2one('stock.lot', string="Lot/Serial")
    expiration_date = fields.Date(string="Expiration Date")
    margin = fields.Float(string="Margin", compute='_compute_margin', digits="Product Price", store=True)
    purchase_price = fields.Float(string="Cost")

    @api.depends('price_subtotal', 'quantity', 'purchase_price')
    def _compute_margin(self):
        for line in self:
            line.margin = 0
            if line.move_id.move_type in ['out_invoice', 'out_refund']:
                line.margin = line.price_subtotal - (line.purchase_price * line.quantity)