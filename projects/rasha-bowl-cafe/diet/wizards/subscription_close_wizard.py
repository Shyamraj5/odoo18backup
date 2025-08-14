# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SubscriptionCloseWizard(models.TransientModel):
    _name = 'subscription.close.wizard'
    _description = 'Subscription Close Wizard'

    close_reason = fields.Many2one('subscription.package.stop', string='Close Reason')
    closed_by = fields.Many2one('res.users', string='Closed By', default=lambda self: self.env.user)
    close_date = fields.Date(string='Closed On', default=lambda self: fields.Date.today())
    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')

    def button_submit(self):
        self.ensure_one()
        this_sub_id = self.env.context.get('active_id')
        sub = self.env['diet.subscription.order'].search([('id', '=', this_sub_id)])
        sub.is_closed = True
        sub.close_reason = self.close_reason
        sub.closed_by = self.closed_by
        sub.close_date = self.close_date
        meal_with_driver_order = sub.meal_calendar_ids.filtered(lambda x: x.date >= self.close_date and x.driver_order_id)
        driver_order_generated_dates = list(set(meal_with_driver_order.mapped('date')))
        driver_order_generated_dates_str = ", ".join(date.strftime('%d-%m-%Y') for date in driver_order_generated_dates) if driver_order_generated_dates else ""
        if driver_order_generated_dates:
            raise UserError(_(f'You cannot close the subscription on this date because there are driver orders scheduled for following dates {driver_order_generated_dates_str}.'))
        if meal_with_driver_order:
            sub.close_date = max(meal_with_driver_order.mapped('date')) + timedelta(days=1)
        meal_calendar_ids = self.env['customer.meal.calendar'].search([
                ('state','!=','freezed'), ('date', '>=', self.close_date),
                ('so_id','=',self.subscription_id.id), ('driver_order_id', '=', False)])
        for calendar in meal_calendar_ids:
            calendar.write({"state" : 'closed',
                           "reason" : f"Cancelled because {self.close_reason.name}"})
        if sub.close_date == fields.Date.today():
            values = {'state': 'closed', 'to_renew': False}
            sub.write(values)

        