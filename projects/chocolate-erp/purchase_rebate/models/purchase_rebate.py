from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rebate_type = fields.Selection([('monthly_discount', 'Monthly Discount'), ('quarterly_discount', 'Quarterly Discount'),
                                    ('yearly_discount', 'Yearly Discount'), ('other_scheme', 'Other Scheme')])

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    list_price = fields.Float()
    monthly_discount = fields.Float()
    quarterly_discount = fields.Float()
    yearly_discount = fields.Float()
    other_scheme = fields.Float()
    total_discount = fields.Float(compute='compute_total_rebate')
    origin_id = fields.Many2one('purchase.order.line')
    

    @api.depends('monthly_discount', 'quarterly_discount', 'yearly_discount', 'other_scheme')
    def compute_total_rebate(self):
        for line in self:
            line.total_discount = line.monthly_discount + line.quarterly_discount + line.yearly_discount + line.other_scheme

    @api.onchange('price_unit')
    def get_list_price(self):
        for line in self:
            if line.price_unit:
                line.list_price = line.price_unit


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rebate_applied = fields.Boolean()

    def apply_discount(self):
        self.rebate_applied = True
        max_sequence = max(self.order_line.mapped('sequence'), default=0)
        discount_list = [
            {
                'display_type': 'line_section',
                'name': "PO Discount",
                'product_qty': 0,
                'sequence': max_sequence + 1
        }
        ]
        for line in self.order_line:
            if line.monthly_discount > 0:
                line.price_unit -= (line.monthly_discount/line.product_qty)
                monthly_discount_item = self.env['product.product'].search([('rebate_type', '=', 'monthly_discount')])
                discount_list.append({
                    'order_id': line.order_id,
                    'price_unit': line.monthly_discount,
                    'product_id': monthly_discount_item.id,
                    'product_qty': 1,
                    'origin_id': line.id,
                    'sequence': max_sequence + 1
                })
            if line.quarterly_discount > 0:
                line.price_unit -= (line.quarterly_discount/line.product_qty)
                quarterly_discount_item = self.env['product.product'].search([('rebate_type', '=', 'quarterly_discount')])
                discount_list.append({
                    'order_id': line.order_id,
                    'price_unit': line.quarterly_discount,
                    'product_id': quarterly_discount_item.id,
                    'product_qty': 1,
                    'origin_id': line.id,
                    'sequence': max_sequence + 1
                })
            if line.yearly_discount > 0:
                line.price_unit -= (line.yearly_discount/line.product_qty)
                yearly_discount_item = self.env['product.product'].search([('rebate_type', '=', 'yearly_discount')])
                discount_list.append({
                    'order_id': line.order_id,
                    'price_unit': line.yearly_discount,
                    'product_id': yearly_discount_item.id,
                    'product_qty': 1,
                    'origin_id': line.id,
                    'sequence': max_sequence + 1
                })
            if line.other_scheme > 0:
                line.price_unit -= (line.other_scheme/line.product_qty)
                other_scheme_item = self.env['product.product'].search([('rebate_type', '=', 'other_scheme')])
                discount_list.append({
                    'order_id': line.order_id,
                    'price_unit': line.other_scheme,
                    'product_id': other_scheme_item.id,
                    'product_qty': 1,
                    'origin_id': line.id,
                    'sequence': max_sequence + 1
                })
        for line in discount_list:
            self.write({'order_line': [(0,0, line)]})

    def remove_rebate_discount(self):
        section_lines = False
        for line in self.order_line.filtered(lambda x: not x.product_id.rebate_type):
            if line.monthly_discount > 0:
                line.price_unit += (line.monthly_discount/line.product_qty)
            if line.quarterly_discount > 0:
                line.price_unit += (line.quarterly_discount/line.product_qty)
            if line.yearly_discount > 0:
                line.price_unit += (line.yearly_discount/line.product_qty)
            if line.other_scheme > 0:
                line.price_unit += (line.other_scheme/line.product_qty)
            rebate_lines = self.order_line.filtered(lambda x: x.origin_id.id == line.id)
            rebate_lines.unlink()
            section_lines = self.order_line.filtered(lambda x: x.display_type == 'line_section' and x.name == 'PO Discount')
        if section_lines:
            self.order_line = [(3, sec_line.id) for sec_line in section_lines]
        self.rebate_applied = False

            

