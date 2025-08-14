from odoo import models, fields, _ 

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_create_invoice(self):
        for record in self:
            pickings = record.picking_ids.filtered(lambda p: p.state == 'done' and p.picking_type_id.code == 'incoming')
            invoiced_pickings = self.env['account.move'].search([
                ('id', 'in', record.invoice_ids.ids)
            ]).picking_ids
            uninvoiced_pickings = pickings - invoiced_pickings
        self = self.with_context(default_picking_ids=uninvoiced_pickings.ids)
        return super(PurchaseOrder, self).action_create_invoice()
