from  odoo import models, fields, api, _


class StockLot(models.Model):
    _inherit = 'stock.lot'

    source_branch_id = fields.Many2one('res.company', string="Branch")
    is_branch_sale = fields.Boolean(string="Is Branch Sale", default=False)
    margin = fields.Float(string="Margin")
    source_lot_id = fields.Many2one('stock.lot', string="Source Lot")