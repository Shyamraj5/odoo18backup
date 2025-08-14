
from odoo import models, fields, _
from odoo.exceptions import UserError


class SubscriptionPlan(models.Model):
    _name = 'special.offer'
    _description = 'Special Offers'


    title = fields.Char(string = 'Title')
    image = fields.Binary(string ='Image')
    description = fields.Text(string = 'Description')
    start_date = fields.Date(string ='Start Date')
    end_date = fields.Date(string ='End Date')
    state = fields.Selection([('draft', 'Draft'),
                                    ('confirm', 'Confirm')], default='draft', string ="Offer Status")
    

    def action_confirm(self):
        for offer in self:
            offer.state = 'confirm'

    def action_reset_to_draft(self):
        for offer in self:
            offer.state = 'draft'

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(SubscriptionPlan, self).unlink()