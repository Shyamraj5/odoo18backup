from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one(
        "stock.lot",
        "Lot",
        copy=False,
        compute="_compute_lot_id",
        store=True,
        readonly=False,
    )
    lot_domain = fields.Char(compute="_compute_lot_domain", store=True)

    @api.depends('product_id')
    def _compute_lot_domain(self):
        for line in self:
            if line.product_id:
                stock_quants = self.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                               ('location_id.usage', '=', 'internal'),
                                                               ('company_id', '=', line.company_id.id)])
                lot_ids = stock_quants.mapped('lot_id').ids
                if lot_ids:
                    line.lot_domain = [('id', 'in', lot_ids)]
            else:
                line.lot_domain = [('id', '=', False)]

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.lot_id:
            vals["restrict_lot_id"] = self.lot_id.id
        return vals

    @api.depends("product_id")
    def _compute_lot_id(self):
        for sol in self:
            if sol.product_id != sol.lot_id.product_id:
                sol.lot_id = False

    @api.depends('lot_id')
    def _compute_purchase_price(self):
        lot_lines = self.filtered('lot_id')
        for line in lot_lines:
            if line.lot_id and line.lot_id.is_branch_sale:
                product_cost = line.product_id.uom_id._compute_price(
                    line.lot_id.standard_price + line.lot_id.margin,    
                    line.product_uom
                )
                line.purchase_price = line._convert_to_sol_currency(
                    product_cost,
                    line.product_id.cost_currency_id
                )
            else:
                product_cost = line.product_id.uom_id._compute_price(
                    line.lot_id.standard_price,
                    line.product_uom
                )
                line.purchase_price = line._convert_to_sol_currency(
                    product_cost,
                    line.product_id.cost_currency_id
                )

        return super(SaleOrderLine, self - lot_lines)._compute_purchase_price()