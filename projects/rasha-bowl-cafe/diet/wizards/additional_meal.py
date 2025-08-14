from odoo import models, fields, api
from datetime import timedelta


class AdditionalMealWizard(models.TransientModel):
    _name = 'additional.meal.wizard'
    _description = 'Additional Meal Wizard'

    subscription_order_id = fields.Many2one('diet.subscription.order')
    line_ids = fields.One2many('additional.meal.wizard.line', 'additional_meal_id')

    def add(self):
        order = self.subscription_order_id
        order.write({
            'addtional_meals_config_ids': [
                (0, 0, {
                    'meal_id': line.meal_id.id,
                    'price': line.price,
                    'count': line.count,
                    'meal_category_id': line.meal_category_id.id,
                }) for line in self.line_ids
            ]
        })
        order._compute_amount()

        has_main_calendar = order.meal_calendar_ids.filtered(lambda m: not m.is_additional_meal)
        if has_main_calendar:
            start_date = fields.Date.today()
            while start_date <= order.end_date:
                day_of_date = str(start_date.weekday())
                schedule_line = False
                shift = False
                address = False

                day_shifts = order.partner_id.shift_ids.filtered(lambda s: s.period == 'day_of_week')
                schedule_line = day_shifts.filtered(lambda s: s.day_of_week == day_of_date)
                shift = schedule_line.shift_type if schedule_line else False
                address = schedule_line.address_id if schedule_line else False

                if not schedule_line:
                    range_shifts = order.partner_id.shift_ids.filtered(lambda s: s.period == 'date_range')
                    schedule_line = range_shifts.filtered(lambda s: s.from_date <= start_date <= s.to_date)
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False

                if not schedule_line:
                    shift = order.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                    address = order.partner_id.customer_address_id

                day_off_map = {
                    '0': not order.monday,
                    '1': not order.tuesday,
                    '2': not order.wednesday,
                    '3': not order.thursday,
                    '4': not order.friday,
                    '5': not order.saturday,
                    '6': not order.sunday,
                }
                is_off_day = day_off_map.get(day_of_date, False)

                if not is_off_day:
                    for line in self.line_ids:
                        for i in range(line.count):
                            self.env['customer.meal.calendar'].sudo().create({
                                "date": start_date,
                                "partner_id": order.partner_id.id,
                                "so_id": order.id,
                                "meal_category_id": line.meal_category_id.id,
                                "plan_category_id": order.plan_category_id.id,
                                "shift_id": shift.id if shift else False,
                                "meal_id": line.meal_id.id,
                                "is_paid_day": True,
                                "is_additional_meal": True,
                            })._onchange_state()
                else:
                    self.env['customer.meal.calendar'].sudo().create({
                        "date": start_date,
                        "partner_id": order.partner_id.id,
                        "so_id": order.id,
                        "state": 'off_day',
                        "off_day": True,
                        "is_additional_meal": True,
                    })

                start_date += timedelta(days=1)


class AdditionalMealWizardLine(models.TransientModel):
    _name = 'additional.meal.wizard.line'
    _description = 'Additional Meal Wizard Line'

    additional_meal_id = fields.Many2one('additional.meal.wizard')
    meal_id = fields.Many2one('product.template', string='Meal')
    price = fields.Float(string='Price/ Day')
    count = fields.Integer(string='Count', default=1)
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')



    

