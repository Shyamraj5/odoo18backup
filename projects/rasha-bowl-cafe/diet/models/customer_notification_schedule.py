from odoo import models, fields, _ 
from datetime import timedelta
from odoo.exceptions import UserError


class CustomerNotificationSchedule(models.Model):
    _name = 'customer.notification.schedule'
    _description = 'Customer Notification Schedule'
    
    name = fields.Char('Name', default="New")
    customer_gender_filter = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('all', 'All'),
    ], string='Customer Gender Filter')
    title = fields.Char(string="Title")
    customer_ids = fields.Many2many('res.partner', string="Customer", domain=[('parent_id', '=', False)])
    message = fields.Text(string="Message")
    photo = fields.Binary(string="Photo", attachment=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], default='draft')
    schedule_type = fields.Selection([
        ('datetime', 'Date & Time'),
        ('daytime', 'Day & Time'),
        ('monthly', 'Every Month')
    ], string='Schedule Type', default='datetime')
    scheduled_datetime = fields.Datetime('Datetime')
    sunday = fields.Boolean('Sunday')
    monday = fields.Boolean('Monday')
    tuesday = fields.Boolean('Tuesday')
    wednesday = fields.Boolean('Wednesday')
    thursday = fields.Boolean('Thursday')
    friday = fields.Boolean('Friday')
    saturday = fields.Boolean('Saturday')
    repeat_every_week = fields.Boolean('Repeat Every Week')
    scheduled_month_day = fields.Integer('Day of Month')
    scheduled_time = fields.Float('Time')
    notification_ids = fields.One2many('customer.notification', 'schedule_id', string='Notifications')

    def activate(self):
        for schedule in self:
            schedule.write({'state': 'active'})

    def deactivate(self):
        for schedule in self:
            schedule.write({'state': 'inactive'})
        
    def reset_draft(self):
        for schedule in self:
            schedule.write({'state': 'draft'})

    def process_notifications(self):
        schedules_to_process = self.env['customer.notification.schedule'].search([
            ('state', '=', 'active'),
        ])
        for schedule in schedules_to_process:
            is_today = False
            is_time = False
            if schedule.schedule_type == 'datetime':
                if schedule.scheduled_datetime.date() == fields.Date.today():
                    is_today = True
            elif schedule.schedule_type == 'daytime':
                today = fields.Date.today()
                today_day = today.strftime('%A').lower()
                if schedule.sunday and today_day == 'sunday':
                    is_today = True
                elif schedule.monday and today_day == 'monday':
                    is_today = True
                elif schedule.tuesday and today_day == 'tuesday':
                    is_today = True
                elif schedule.wednesday and today_day == 'wednesday':
                    is_today = True
                elif schedule.thursday and today_day == 'thursday':
                    is_today = True
                elif schedule.friday and today_day == 'friday':
                    is_today = True
                elif schedule.saturday and today_day == 'saturday':
                    is_today = True
            elif schedule.schedule_type == 'monthly':
                if schedule.scheduled_month_day == fields.Date.today().day:
                    is_today = True
            if is_today:
                if schedule.schedule_type == 'datetime':
                    scheduled_time = schedule.scheduled_datetime.time()
                else:
                    scheduled_time = fields.Datetime.from_string(f"{fields.Date.today()} {schedule.scheduled_time}").time()
                t_minus_30 = fields.Datetime.now() - timedelta(minutes=30)
                t_plus_30 = fields.Datetime.now() + timedelta(minutes=30)
                if t_minus_30.time() <= scheduled_time <= t_plus_30.time():
                    is_time = True
            if is_time:
                notification = self.env['customer.notification'].create({
                    'title': schedule.title,
                    'message': schedule.message,
                    'photo': schedule.photo,
                    'customer_ids': [(6, 0, schedule.customer_ids.ids)],
                    'notification_type': 'bulk',
                    'notification_category': 'custom',
                    'schedule_id': schedule.id,
                    'customer_gender_filter': schedule.customer_gender_filter
                })
                notification.send()
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(CustomerNotificationSchedule, self).unlink()
