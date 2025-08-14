from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import datetime,timedelta, date
import base64

class CustomerMealCalendar(models.Model):
    _name = 'customer.meal.calendar'
    _description = 'Customer Meal Calendar'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'meal_category_id'  

    day = fields.Integer('Day', compute='_compute_day', store=True, precompute=True)
    date = fields.Date('Date', tracking=True, copy=True)
    start_date = fields.Date('Start Date', compute='_compute_dates', store=True)
    end_date = fields.Date('End Date', compute='_compute_dates', store=True)
    weekday = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Weekday', compute='_compute_day', store=True, tracking =True, precompute=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking =True, copy=True)
    so_id = fields.Many2one('diet.subscription.order', string='SO Id', ondelete='cascade', copy=True)
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', tracking =True, copy=True)
    meal_id = fields.Many2one('product.template', string='Meal', domain=[('is_meal','=',True)], tracking =True, copy=True)
    meal_ids = fields.Many2many('product.template', string='Meals', domain=[('is_meal','=',True)], compute='_compute_meal_id', store=True, precompute=True)
    is_frozen = fields.Boolean('Is Frozen', default =False)
    frozen_for_days = fields.Integer('Frozen For Days')
    frozen_on_date = fields.Date('Frozen On Date')
    plan_category_id =fields.Many2one('plan.category', string ="Plan category", related="so_id.plan_category_id")
    company_id = fields.Many2one('res.company', string= "Company", default = lambda self: self.env.user.company_id, copy=True)
    state = fields.Selection([('active','Active'),('active_with_meal','Active - with meal'),('freezed','Freezed'),('upgraded','Upgraded'),('closed','Closed'),('off_day','Off Day')], string ="State", copy=True)
    reason = fields.Text(string ="Reason")
    off_day = fields.Boolean(string="Is Off Day")
    shift_id = fields.Many2one('customer.shift' ,string="Shift", copy=True)
    address_id = fields.Many2one('res.partner' ,string="Address", copy=True)
    calorie_status = fields.Float(string = "Calorie status",compute='_compute_calorie_status',store=True)
    total_calories = fields.Float(string = "Total calories",compute='_compute_total_calories',store=True)
    target_calories = fields.Float(string = "Target calories",compute='_compute_target_calories',store=True)
    meal_selection_by = fields.Selection([
        ('system', 'SYSTEM'),
        ('customer', 'CUSTOMER'),
        ('user', 'ADMIN')
    ], string='Meal Selection by', default='system')
    is_paid_day = fields.Boolean('Is Paid Day', default=True)
    freezed_calendar_id = fields.Many2one(
        'customer.meal.calendar',
        'Freezed Calendar Entry',
        help='Used to identify against which freezed calendar entry is the current one created',
        copy=False
    )
    delivery_status = fields.Selection([
        ('not_delivered', 'Not Delivered'),
        ('delivered', 'Delivered')
    ], string='Delivery Status', default='not_delivered')
    calendar_color_state = fields.Char('Calendar Color', compute='_compute_calendar_color_state', store=True)
    is_additional_meal = fields.Boolean("Is Additional Meal")

    @api.depends('state', 'delivery_status')
    def _compute_calendar_color_state(self):
        for rec in self:
            if rec.delivery_status == 'delivered':
                rec.calendar_color_state = rec.delivery_status
            else:
                rec.calendar_color_state = rec.state


    def default_get(self, fields_list):
        defaults = super(CustomerMealCalendar, self).default_get(fields_list)
        default_shift = self.env['customer.shift'].search([('is_default', '=', True)], limit=1)
        defaults['shift_id'] = default_shift.id if default_shift else False
        return defaults

    @api.onchange('date','target_calories')
    def _compute_total_calories(self):
        for calendar in self:
            if calendar.date:
                meals = self.env['customer.meal.calendar'].search([('date', '=', calendar.date)])
                total_calories = sum(meal.meal_id.calories for meal in meals if meal.meal_id and meal.meal_id.calories)
                calendar.total_calories = total_calories
            else:
                calendar.total_calories = 0.0

    @api.depends('so_id.calories') 
    def _compute_target_calories(self):
        for record in self:
            if record.so_id:
                record.target_calories = record.so_id.calories 

    @api.depends('total_calories', 'target_calories')
    def _compute_calorie_status(self):
        for record in self:
            if record.target_calories:
                calorie_percentage = (record.total_calories / record.target_calories) * 100
                record.calorie_status = calorie_percentage
            else:
                record.calorie_status = 0.0

    @api.onchange('meal_id')
    def _onchange_state(self):
        for rec in self:
            if rec.meal_id and rec.meal_category_id:
                rec.state = 'active_with_meal'
            elif not rec.meal_id and rec.meal_category_id:
                rec.state = 'active'

    @api.depends('date')
    def _compute_dates(self):
        for rec in self:
            rec.start_date = rec.date
            rec.end_date = rec.date
 
    def _compute_display_name(self):
        for rec in self:
            if rec.state == 'active':
                rec.display_name = f'{rec.meal_category_id.name} - {"Meal not selected"}'
            elif rec.state == 'active_with_meal':
                rec.display_name = f'{rec.meal_category_id.name} - {rec.meal_id.name}'
            elif rec.state == 'freezed':
                 rec.display_name = 'freezed'
            elif rec.state == 'off_day':
                rec.display_name = 'Off Day'
            else:
                rec.display_name = 'Closed/Expired'

    @api.depends('date')
    def _compute_day(self):
        for rec in self:
            if rec.date:
                rec.write({
                    'day': rec.date.day,
                    'weekday': str(rec.date.weekday())
                })
            else:
                rec.write({
                    'day': False,
                    'weekday': False
                })

    @api.depends('date','weekday', 'meal_category_id')
    def _compute_meal_id(self):
        for rec in self:
            meal_ids = self.env['product.template'].search([('meal_category_id','=',rec.meal_category_id.id)])
            if rec.date and rec.weekday == '0' and rec.meal_category_id:
                rec.meal_ids = meal_ids.filtered(lambda x: x.monday)
            elif rec.date and rec.weekday == '1' and rec.meal_category_id:
                rec.meal_ids = meal_ids.filtered(lambda x: x.tuesday)
            elif rec.date and rec.weekday == '2' and rec.meal_category_id:
                rec.meal_ids = meal_ids.filtered(lambda x: x.wednesday)
            elif rec.date and rec.weekday == '3' and rec.meal_category_id:
                rec.meal_ids = meal_ids.filtered(lambda x: x.thursday)
            elif rec.date and rec.weekday == '4' and rec.meal_category_id:
                rec.meal_ids = meal_ids.filtered(lambda x: x.friday)
            elif rec.date and rec.weekday == '5' and rec.meal_category_id:
                rec.meal_ids = meal_ids.filtered(lambda x: x.saturday)
            elif rec.date and rec.weekday == '6' and rec.meal_category_id:
                rec.meal_ids = meal_ids.filtered(lambda x: x.sunday)
            elif rec.meal_category_id:
                rec.meal_ids = meal_ids
            else:
                rec.meal_ids = False
    
    
    
    @api.onchange('meal_id')
    def _onchange_meal_id(self):
        for rec in self:
            rec.meal_selection_by = 'user'
    # this restriction is temporarily removed for data entry purpose
    #         if rec.date:
    #             today = fields.Date.today()
    #             date_diff = (fields.Date.from_string(rec.date)-fields.Date.from_string(today)).days
    #             if date_diff < 3:
    #                 raise UserError('The selected date is two days before today')

    def meal_calender_notification(self):
        meal_calender = self.env['customer.meal.calendar'].search([])
        for rec in meal_calender:
            if not rec.meal_id and rec.meal_category_id:
                date = fields.Date.today().day + 3
                if rec.date.day == date:
                    data = {
                        'notification_type':'single',
                        'notification_category':'custom',
                        'customer_ids':rec.partner_id,
                        'message':f'No meal found in {rec.date} for cateory {rec.meal_category_id.name}'
                    }
                    records = self.env['customer.notification'].create(data)
                
                    records.send()
        return records
            
    def assign_unassigned_address_shift(self):
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)
        tomorrow_1 = today + timedelta(days=2)
        tomorrow_2 = today + timedelta(days=3)
        meal_calendar_ids = self.env['customer.meal.calendar'].search([
            ('date', 'in', [tomorrow, tomorrow_1, tomorrow_2]),
            ('state', 'in', ['active', 'active_with_meal'])
        ])
        updates = []
        for entry in meal_calendar_ids:
            order = entry.so_id
            day_of_date = str(entry.date.weekday())
            day_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                shift.period=='day_of_week'
            )
            schedule_line = False
            shift = False
            address = False
            if not schedule_line:
                schedule_line = day_shifts.filtered(lambda shift:
                    shift.day_of_week == day_of_date
                )
                shift = schedule_line.shift_type if schedule_line else False
                address = schedule_line.address_id if schedule_line else False
            if not schedule_line:
                range_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                    shift.period=='date_range'
                )
                schedule_line = range_shifts.filtered(lambda shift:
                    shift.from_date <= entry.date <= shift.to_date
                )
                shift = schedule_line.shift_type if schedule_line else False
                address = schedule_line.address_id if schedule_line else False
            if not schedule_line:
                shift = order.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                address = order.partner_id.customer_address_id
            if shift and entry.shift_id != shift:
                updates.append((entry, {'shift_id': shift.id}))
            if address and entry.address_id != address:
                updates.append((entry, {'address_id': address.id}))

        for entry, vals in updates:
            entry.write(vals)

        return True

    def unlink(self):
        for calendar in self:
            if calendar.driver_order_id:
                raise UserError(_('You cannot delete a calendar entry that is associated with a driver order.'))
        return super(CustomerMealCalendar, self).unlink()
