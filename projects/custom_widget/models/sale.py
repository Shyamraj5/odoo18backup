from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    my_number = fields.Integer(string="Number")
    is_sale_order = fields.Boolean(string="Is Sale Order", default=False,compute="_compute_is_sale_order")
    text = fields.Text(string="Text")


    @api.depends('state')
    def _compute_is_sale_order(self):
        for rec in self:
            if rec.state == 'sale':
                rec.is_sale_order = True
            else:
                rec.is_sale_order = False