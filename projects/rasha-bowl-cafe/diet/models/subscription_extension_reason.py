from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError

class SubscriptionExtensionReason(models.Model):
    _name = 'subscription.extension.reason'
    _description = 'Subscription Extension Reason'
    
    name = fields.Char('Reason')


    @api.constrains('name')
    def _constrains_name(self):
        for reason in self:
            query = f"""SELECT name FROM subscription_extension_reason WHERE id != {reason.id}"""
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            for name in result:
                if reason.name.lower() == name[0].lower():
                    raise ValidationError("Reason already exists")
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(SubscriptionExtensionReason, self).unlink()