from odoo import models, fields, _
import random
import string

class ResetpasswordWizard(models.TransientModel):
    _name = "reset.password.wizard"
    _description = "Wizard for reset password"

    password = fields.Char(string="New Password")
    customer_id = fields.Many2one('res.partner', string="Customer")
    send_by_sms = fields.Boolean(string="Send by sms", default=False)

    def generate_password(self):
        characterList = string.ascii_letters + string.digits
        password = ''.join(random.sample(characterList, 8))
        return {
            "name": _("Reset password"),
            "res_model": "reset.password.wizard",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "target": "new",
            "context": {
                'default_customer_id': self.customer_id.id,
                'default_password': password,
                'default_send_by_sms': self.send_by_sms
            },
        }

    def reset_password(self):
        self.customer_id.diet_app_password = self.password
        if self.send_by_sms:
            notification = self.env['customer.notification'].create({
                'notification_type': 'single',
                'notification_category': 'custom',
                'customer_ids': self.customer_id,
                'title': 'Password Reset',
                'message': f"Password has been updated your new password is {self.password}"
            })
            if notification:
                notification.send()
        