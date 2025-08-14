from odoo import models, fields, api, _

class CustomerNotificationWizard(models.TransientModel):
    _name = "customer.notification.wizard"
    _description = "Wizard for customer notification"

    customer_id = fields.Many2one('res.partner', string="Customer")
    title = fields.Char(string="Title")
    description = fields.Text(string="Description")
    photo = fields.Binary(string="Photo")

    def action_submit(self):
        notifications = self.env['customer.notification'].create({
            'customer_ids': self.customer_id.ids,
            'title': self.title,
            'message':self.description,
            'photo': self.photo
        })
        if notifications:
            notifications.send()
        
