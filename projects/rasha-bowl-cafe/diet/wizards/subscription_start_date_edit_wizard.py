from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class SubscriptionStartDateEditWizard(models.TransientModel):
    _name = 'subscription.start.date.edit.wizard'
    _description = 'Subscription Start Date Edit Wizard'

    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    new_start_date = fields.Date(string='New Start Date')
    new_end_date = fields.Date(string='New End Date')

    @api.onchange('subscription_id','new_start_date')
    def _onchange_end_date(self):
        if self.new_start_date and self.subscription_id.plan_choice_id:
            start_date = fields.Datetime.from_string(self.new_start_date)
            week = 7
            excluded_weekdays = []
            if not self.subscription_id.monday:
                excluded_weekdays.append(0)
            if not self.subscription_id.tuesday:
                excluded_weekdays.append(1)
            if not self.subscription_id.wednesday:
                excluded_weekdays.append(2)
            if not self.subscription_id.thursday:
                excluded_weekdays.append(3)
            if not self.subscription_id.friday:
                excluded_weekdays.append(4)
            if not self.subscription_id.saturday:
                excluded_weekdays.append(5)
            if not self.subscription_id.sunday:
                excluded_weekdays.append(6)
            end_date = self.subscription_id._get_end_date(excluded_weekdays, self.subscription_id.plan_choice_id.no_of_day, start_date)
            self.new_end_date = end_date.date()
        else:
            self.new_end_date = False

    def update_start_date(self):
        today = fields.Date.today()
        buffer_days = int(self.env['ir.config_parameter'].sudo().get_param('diet.start_date_edit_buffer', default=0))

        if today <= self.new_start_date <= today + timedelta(days= buffer_days):
            raise UserError(_('The new start date must be at least %s days from today!') % buffer_days)
        if self.subscription_id.state in ['paid','in_progress']:
            self.subscription_id.change_subscription_start_date(self.new_start_date, self.new_end_date)
        else:
            raise UserError(_('You can only change the start date of a confirmed subscription before meal calendar generation!'))
        return {'type': 'ir.actions.act_window_close'}