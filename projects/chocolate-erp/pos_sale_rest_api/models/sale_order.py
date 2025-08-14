from odoo import models, fields


class DeliveryPriority(models.Model):
    _name = 'delivery.priority'
    _description = 'Delivery Priority'

    name = fields.Char(required=True)
    pos_id = fields.Integer('Id in B2B Sale App')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_priority_id = fields.Many2one('delivery.priority')
    delivery_description = fields.Text()
    django_id = fields.Integer('Django Sale Order ID')
    django_quotation_id = fields.Integer()


    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            pickings_ids = rec.picking_ids
            for pickings in pickings_ids:
                pickings.update({'delivery_priority_id': rec.delivery_priority_id.id,'delivery_description':rec.delivery_description})
        return res



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    django_sale_line_id = fields.Integer('Django Sale Order Line ID')
    django_quotation_line_id = fields.Integer()