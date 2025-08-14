from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError



class ExtendDaysMinus(models.TransientModel):
    _name = 'extent.minus.days.wizard'
    _description = 'Minus Extension Wizard'

    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    days = fields.Integer('Days', default=1)
    current_extended_days = fields.Integer(related='subscription_id.additional_days',string="Current Additional Days")

    def button_confirm_reduction(self):
        if self.days > self.subscription_id.additional_days:
            raise UserError(_("Days to reduce cannot exceed the extended days."))
        if self.days < 1:
            raise UserError(_("Days must be greater than 0."))

        new_end_date = self.subscription_id.end_date - timedelta(days=self.days)
        if new_end_date < fields.Date.today():
            raise UserError(_("The new end date cannot be in the past."))

        order = self.subscription_id

        end_date = order.end_date
        reduced_days = self.days

        while reduced_days > 0:
            calendar_entries = self.env['customer.meal.calendar'].search([
                ('so_id', '=', order.id),
                ('date', '=', end_date)
            ])
            off_day = calendar_entries.filtered(lambda cal:cal.off_day == True)

            if calendar_entries and off_day:
                end_date -= timedelta(days=1)
                calendar_entries.unlink()
                continue

            calendar_entries.unlink()
            end_date -= timedelta(days=1)
            reduced_days -= 1

        order.end_date = new_end_date
        order.additional_days -= self.days

        order._compute_amount()
        order.message_post(
            body=_(f"Subscription reduced by {self.days} days.")
        )
