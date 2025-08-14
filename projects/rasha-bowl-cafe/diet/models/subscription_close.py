# -*- coding: utf-8 -*-


from odoo import models, fields, _ 
from odoo.exceptions import UserError


class SubscriptionPackageStopReason(models.Model):
    _name = "subscription.package.stop"
    _description = "Subscription Package Stop Reason"
    _order = 'sequence'

    sequence = fields.Integer(help="Determine the display order", index=True,
                              string='Sequence')
    name = fields.Char(string='Reason', required=True)

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(SubscriptionPackageStopReason, self).unlink()