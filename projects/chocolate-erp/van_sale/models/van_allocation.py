from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VanAllocationRequest(models.Model):
    _name = 'van.allocation.request'
    _description = 'Van Allocation Request'

    user_id = fields.Many2one('res.users', 'Salesperson')
    van_id = fields.Many2one('van.detail', 'Van')
    van_company_id = fields.Many2one(related='van_id.company_id')
    date = fields.Date(default=fields.Date.today())
    order_line = fields.One2many('van.allocation.request.line', 'allocation_request_id')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('cancel', 'Cancelled')
        ], string="Status", default='draft',
    )
    so_id = fields.Many2one('sale.order')

    @api.constrains("lot_id","product_id")
    def _check_lot_required(self):
        for line in self:
            if line.product_id.tracking == 'lot' and not line.lot_id:
                raise ValidationError(
                    "The Lot/Serial Number is required for the product '%s' because it is tracked by lot."
                    % line.product_id.display_name
                )

    def create_sale_order(self):
        for rec in self:
            sale_order = self.env['sale.order'].create({
                'partner_id': rec.van_id.company_id.partner_id.id,
                'date_order': rec.date,
            })
            for line in rec.order_line:
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'lot_id': line.lot_id.id,
                    'product_uom': line.uom_id.id
                })
            rec.so_id = sale_order.id
            rec.state = 'confirm'
        return sale_order

    def view_sale_order(self):
        """
        Action to open the related sale order form view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.so_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

class VanAllocationRequestLine(models.Model):
    _name = 'van.allocation.request.line'
    _description = 'Van Allocation Line'

    allocation_request_id = fields.Many2one('van.allocation.request')
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one("stock.lot", string="Lot/Serial Number", domain="[('product_id', '=', product_id)]",)
    quantity = fields.Float()
    uom_id = fields.Many2one('uom.uom')

