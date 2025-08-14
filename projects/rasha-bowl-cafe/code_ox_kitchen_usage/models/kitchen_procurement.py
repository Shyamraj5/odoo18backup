from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from collections import defaultdict
from odoo.tools import float_compare, float_is_zero, frozendict, split_every, format_date


class KitchenProcurement(models.Model):
    _name = 'kitchen.procurement'
    _description = 'Kitchen Procurement'

    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Location')
    qty_on_hand = fields.Float('On Hand', readonly=True, compute='_compute_qty', digits='Product Unit of Measure')
    product_min_qty = fields.Float('Min')
    product_max_qty = fields.Float('Max')
    qty_to_order = fields.Float('To Order')
    product_uom_id = fields.Many2one('uom.uom',string='UoM', readonly=True)

    @api.model
    def default_get(self, default_field):
        values = super(KitchenProcurement, self).default_get(default_field)
        if self.env['ir.config_parameter'].sudo().get_param('code_ox_kitchen_usage.location_id'):
            values['location_id']= int(self.env['ir.config_parameter'].sudo().get_param('code_ox_kitchen_usage.location_id'))
        return values

    @api.onchange('product_min_qty')
    def onchange_product_min_qty(self):
        for record in self:
            record.product_max_qty = record.product_min_qty

    @api.onchange('product_id')
    def get_product_uom(self):
        for rec in self:
            product = rec.product_id
            uom = product.uom_id
            if uom:
                rec.product_uom_id = uom.id

    @api.constrains('product_max_qty','product_min_qty')
    def _check_min_max_qty(self):
        for rec in self:
            if rec.product_min_qty > rec.product_max_qty:
                raise ValidationError("Min Qty Cannot Be Greater Than Max Qty")
            
    @api.depends('product_id', 'location_id')
    def _compute_qty(self):
        for record in self:
            if not record.product_id or not record.location_id:
                record.qty_on_hand = 0.0
                continue

            stock_quant = self.env['stock.quant'].search([
                ('product_id', '=', record.product_id.id),
                ('location_id', '=', record.location_id.id)
            ], limit=1)

            record.qty_on_hand = stock_quant.quantity if stock_quant else 0.0

