from odoo import models, fields, api

class StockWarehouseOrderpoint(models.Model):
    _name = 'stock.warehouse.orderpoint'
    _inherit = ['stock.warehouse.orderpoint', 'mail.thread', 'mail.activity.mixin']

    trigger = fields.Selection(
        default='manual'
    )

    @api.model
    def check_replenishment_notifications(self):
        replenishment_group = self.env.ref('replenishment_notification.group_repleneishment_notification')
        if not replenishment_group:
            return
        users = replenishment_group.users
        if not users:
            return
        
        orderpoints = self.search([])
        for orderpoint in orderpoints:
            if orderpoint.qty_on_hand <= orderpoint.product_min_qty:  
                message = "Replenishment needed for %s" % orderpoint.product_id.display_name
                note = "Quantity on hand for %s has reached the minimum quantity" % orderpoint.product_id.display_name

                for notification_user in users:
                    self.env['mail.activity'].create({
                        'res_model_id': self.env['ir.model']._get_id('stock.warehouse.orderpoint'),
                        'res_id': orderpoint.id,
                        'user_id': notification_user.id,
                        'summary': message,
                        'note': note,
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    })

                    notification_user.sudo().notify_warning(
                        message=message,
                        title="Replenishment Notification",
                        sticky=False
                    )
