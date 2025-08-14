from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SubscriptionExtensionWizard(models.TransientModel):
    _name = 'subscription.extension.wizard'
    _description = 'Subscription Extension Wizard'
    
    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    current_end_date = fields.Date('Current End Date', related='subscription_id.end_date')
    days = fields.Integer('Days', default=1)
    subscription_extension_reason_id = fields.Many2one('subscription.extension.reason', string='Subscription Reason')
    require_payment = fields.Boolean('Require Payment')

    def button_confirm(self):
        if self.days < 1:
            raise UserError(_("Days must be greater than 0."))
        current_end_date = self.current_end_date
        new_end_date = self.current_end_date + timedelta(days=self.days)
        start_date = self.current_end_date + timedelta(days=1)
        order = self.subscription_id
        ramdan_start_date = self.env.company.ramdan_start_date
        ramdan_end_date = self.env.company.ramdan_end_date
        while start_date <= new_end_date:
            if (
                ramdan_start_date
                and ramdan_end_date
                and ramdan_start_date <= start_date <= ramdan_end_date
            ):
                is_ramdan = True
            else:
                is_ramdan = False
            day_of_date = str(start_date.weekday())
            day_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                shift.period=='day_of_week'
            )
            schedule_line = False
            shift = False
            address = False
            if not schedule_line:
                schedule_line = day_shifts.filtered(lambda shift:
                    shift.day_of_week == 'day_of_date'
                )
                shift = schedule_line.shift_type if schedule_line else False
                address = schedule_line.address_id if schedule_line else False
            if not schedule_line:
                range_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                    shift.period=='date_range'
                )
                schedule_line = range_shifts.filtered(lambda shift:
                    shift.from_date <= start_date <= shift.to_date
                )
                shift = schedule_line.shift_type if schedule_line else False
                address = schedule_line.address_id if schedule_line else False
            if not schedule_line:
                shift = order.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                address = order.partner_id.customer_address_id
            if is_ramdan:
                if order.plan_id.is_ramdan_plan:
                    available_meal = order.meal_count_ids
                    plan = order.plan_id
                else:
                    available_meal = order.ramdan_meal_count_ids
                    plan = order.ramdan_plan_id
            else:
                if order.plan_id.is_ramdan_plan:
                    available_meal = order.ramdan_meal_count_ids
                    plan = order.ramdan_plan_id
                else:
                    available_meal = order.meal_count_ids
                    plan = order.plan_id
            meal_category_ids=[]
            for record in available_meal:
                if record.additional_count > 0:
                    category_ids=record.meal_category_id.ids
                    meal_category_ids.append(category_ids[0])
            off_day = False
            if day_of_date == '0':
                off_day = not order.monday
            elif day_of_date == '1':
                off_day = not order.tuesday
            elif day_of_date == '2':
                off_day = not order.wednesday
            elif day_of_date == '3':
                off_day = not order.thursday
            elif day_of_date == '4':
                off_day = not order.friday
            elif day_of_date == '5':
                off_day = not order.saturday
            elif day_of_date == '6':
                off_day = not order.sunday
            if off_day:
                self.env['customer.meal.calendar'].create({
                    "date": start_date,
                    "partner_id": order.partner_id.id,
                    "so_id": order.id,
                    "state" :'off_day',
                    "off_day" :off_day,
                })
                new_end_date += timedelta(days=1)
                start_date += timedelta(days=1)
            else:
                for i in meal_category_ids:
                    meal_count = available_meal.filtered(lambda meal: meal.meal_category_id.id == i)
                    for j in range(int(meal_count.additional_count)):
                        # for line in order.plan_id.meal_config_ids:
                        #     if line.meal_category_id.id == i:
                        #         deafult_meal_id = False
                        #         break
                        meal_calendar = self.env['customer.meal.calendar'].create({
                            "date": start_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":i,
                            "plan_category_id": order.plan_category_id.id,
                            "shift_id" : shift.id if shift else False,
                            "address_id" : address.id if address else False,
                            "meal_id": False,
                            "is_paid_day": True if self.require_payment else False,
                        })
                        meal_calendar._onchange_state()
                start_date += timedelta(days=1)
        order.end_date = new_end_date
        order.additional_days += self.days
        order.apply_default_meals()
        order._compute_amount()
        order.message_post(
            body=_(f"Subscription Extended for {self.days} days because {self.subscription_extension_reason_id.name}.")
        )
        upcoming_subscriptions = self.env['diet.subscription.order'].search([
            ('partner_id', '=', order.partner_id.id),
            ('id', '!=', order.id),
            ('state', 'in', ['paid', 'in_progress']),
            ('actual_start_date', '>=', current_end_date)
        ])
        this_new_end_date = new_end_date
        for upcoming_subscription in upcoming_subscriptions:
            if this_new_end_date < upcoming_subscription.actual_start_date:
                break
            if not upcoming_subscription.is_subscription_moved: 
                upcoming_subscription.write({
                    'is_subscription_moved': True,
                    'previous_start_date': upcoming_subscription.actual_start_date
                })
            upcoming_sub_current_start_date = upcoming_subscription.actual_start_date
            upcoming_sub_new_start_date = upcoming_subscription.get_new_start_date(this_new_end_date + timedelta(days=1))
            calendar_ids_to_delete = upcoming_subscription.meal_calendar_ids.filtered(
                lambda cal: upcoming_sub_current_start_date <= cal.date < upcoming_sub_new_start_date
            )
            delivery_days = len(list(set(calendar_ids_to_delete.filtered(lambda cal: cal.state in ['active', 'active_with_meal']).mapped('date'))))
            calendar_ids_to_delete.sudo().unlink()
            # find end date
            upcoming_subscription_end_date = upcoming_subscription.end_date
            day = 0
            calendar_date = upcoming_subscription_end_date + timedelta(days=1)
            if delivery_days == 0:
                excluded_weekdays = []
                if not upcoming_subscription.monday:
                    excluded_weekdays.append(0)
                if not upcoming_subscription.tuesday:
                    excluded_weekdays.append(1)
                if not upcoming_subscription.wednesday:
                    excluded_weekdays.append(2)
                if not upcoming_subscription.thursday:
                    excluded_weekdays.append(3)
                if not upcoming_subscription.friday:
                    excluded_weekdays.append(4)
                if not upcoming_subscription.saturday:
                    excluded_weekdays.append(5)
                if not upcoming_subscription.sunday:
                    excluded_weekdays.append(6)
                calendar_date = upcoming_subscription._get_end_date(excluded_weekdays, upcoming_subscription.plan_choice_id.no_of_day, upcoming_sub_new_start_date) + timedelta(days=1)
        
            ramdan_start_date = self.env.company.ramdan_start_date
            ramdan_end_date = self.env.company.ramdan_end_date
            while day < delivery_days:
                if (
                    ramdan_start_date
                    and ramdan_end_date
                    and ramdan_start_date <= start_date <= ramdan_end_date
                ):
                    is_ramdan = True
                else:
                    is_ramdan = False
                day_of_date = str(calendar_date.weekday())
                day_shifts = upcoming_subscription.partner_id.shift_ids.filtered(lambda shift:
                    shift.period=='day_of_week'
                )
                schedule_line = False
                shift = False
                address = False
                if not schedule_line:
                    schedule_line = day_shifts.filtered(lambda shift:
                        shift.day_of_week == 'day_of_date'
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    range_shifts = upcoming_subscription.partner_id.shift_ids.filtered(lambda shift:
                        shift.period=='date_range'
                    )
                    schedule_line = range_shifts.filtered(lambda shift:
                        shift.from_date <= calendar_date <= shift.to_date
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    shift = upcoming_subscription.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                    address = upcoming_subscription.partner_id.customer_address_id
                
                if is_ramdan:
                    if upcoming_subscription.plan_id.is_ramdan_plan:
                        available_meal = upcoming_subscription.meal_count_ids
                        plan = upcoming_subscription.plan_id
                    else:
                        available_meal = upcoming_subscription.ramdan_meal_count_ids
                        plan = upcoming_subscription.ramdan_plan_id
                else:
                    if upcoming_subscription.plan_id.is_ramdan_plan:
                        available_meal = upcoming_subscription.ramdan_meal_count_ids
                        plan = upcoming_subscription.ramdan_plan_id
                    else:
                        available_meal = upcoming_subscription.meal_count_ids
                        plan = upcoming_subscription.plan_id
                meal_category_ids=[]
                for record in available_meal:
                    if record.additional_count > 0:
                        category_ids=record.meal_category_id.ids
                        meal_category_ids.append(category_ids[0])
                is_off_day = upcoming_subscription.check_off_day(calendar_date)
                if is_off_day:
                    self.env['customer.meal.calendar'].create({
                        "date": calendar_date,
                        "partner_id": upcoming_subscription.partner_id.id,
                        "so_id": upcoming_subscription.id,
                        "state" :'off_day',
                        "off_day" :is_off_day,
                    })
                else:
                    for i in meal_category_ids:
                        meal_count = available_meal.filtered(lambda meal: meal.meal_category_id.id == i)
                        for j in range(int(meal_count.additional_count)):
                            # for line in upcoming_subscription.plan_id.meal_config_ids:
                            #     if line.meal_category_id.id == i:
                            #         deafult_meal_id = line.meal_ids[0].id if line.meal_ids else False
                            #         break
                            meal_calendar = self.env['customer.meal.calendar'].create({
                                "date": calendar_date,
                                "partner_id": upcoming_subscription.partner_id.id,
                                "so_id": upcoming_subscription.id,
                                "meal_category_id":i,
                                "plan_category_id": upcoming_subscription.plan_category_id.id,
                                "shift_id" : shift.id if shift else False,
                                "address_id" : address.id if address else False,
                                "meal_id": False,
                            })
                            meal_calendar._onchange_state()
                            upcoming_subscription.apply_default_meals_by_date_range(calendar_date, calendar_date)
                    day += 1
                calendar_date += timedelta(days=1)
            upcoming_subscription.with_context(skip_subscription_overlap_check=True).write({
                'actual_start_date': upcoming_sub_new_start_date,
                'end_date': calendar_date - timedelta(days=1),
            })
            upcoming_subscription.with_context(skip_base_price_calculation=True)._compute_amount()
        if self.require_payment:
            base_price = order.total
            base_per_day_price = base_price / order.total_days if order.total_days else 0
            total_price = base_per_day_price * self.days

            product = self.env['product.product'].search([
                ('plan_id', '=', order.plan_id.id), 
                ('is_plan', '=', True)
            ], limit=1)
            if not product:
                raise UserError(_("Related product not found for this plan."))
            invoice_line = {
                'product_id': product.id,
                'name': f"{order.plan_id.name} - Extension",
                'quantity': 1,
                'price_unit': total_price,
            }   
            invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': order.partner_id.id,
                'customer_so_line_id': order.id,
                'invoice_origin': order.order_number,
                'invoice_date': fields.Date.today(),
                'payment_platform': order.payment_type,
                'invoice_line_ids': [(0, 0, invoice_line)]
            }) 
            invoice.action_post()
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }