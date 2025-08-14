from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import timedelta, time, datetime
from lxml import etree
from odoo.exceptions import ValidationError
from pytz import timezone

class SubscriptionEditWizard(models.TransientModel):
    _name = 'subscription.edit.wizard'
    _description = 'Subscription Edit Wizard'
    
    subscription_id = fields.Many2one(
        comodel_name='diet.subscription.order',
        string='Subscription'
    )
    sunday = fields.Boolean('Sunday')
    monday = fields.Boolean('Monday')
    tuesday = fields.Boolean('Tuesday')
    wednesday = fields.Boolean('Wednesday')
    thursday = fields.Boolean('Thursday')
    friday = fields.Boolean('Friday')
    saturday = fields.Boolean('Saturday')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', compute='_compute_end_date')
    protein = fields.Integer('Protein')
    carbohydrates = fields.Integer('Carbohydrates')
    subscribed_days = fields.Integer('Subscribed Days', related='subscription_id.package_days')
    additional_days = fields.Integer('Additional Days')
    available_days = fields.Integer('Available Days', compute='_compute_available_days')
    price = fields.Float('Price', related='subscription_id.grand_total', readonly=True)
    additional_price = fields.Monetary('Manual Additional Price')
    total = fields.Monetary('Total', compute='_compute_total')
    subscription_edit_wizard_line_ids = fields.One2many(
        comodel_name='subscription.edit.wizard.line',
        inverse_name='wizard_id',
        string='Subscription Edit Wizard Lines'
    )
    total_base_meals_amount = fields.Monetary('Total Base Meals Amount', compute='_compute_total_base_meals_amount')
    subscription_edit_wizard_additional_line_ids = fields.One2many(
        comodel_name='subscription.edit.wizard.additional.line',
        inverse_name='wizard_id',
        string='Subscription Edit Wizard Additional Lines'
    )
    currency_id = fields.Many2one('res.currency', string='Currency', related='subscription_id.currency_id')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if (self.start_date >= self.subscription_id.end_date) and (self.subscription_id.actual_start_date != self.subscription_id.end_date):
            raise ValidationError(_("Start date should be less than subscription end date"))
        if self.start_date < fields.Date.today() + relativedelta(days=2):
            raise ValidationError(_("Start date should be greater than or equal to today"))
        if self.start_date < self.subscription_id.actual_start_date:
            raise ValidationError(_("Start date should be greater than or equal to subscription start date"))

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id, view_type, **options)
        if view_type == "form":
            eview = etree.fromstring(res["arch"])
            xml_fields = eview.xpath("//field[@name='start_date']")
            if xml_fields:
                current_time = datetime.now().time()
                user_tz = self.env.context.get('tz') or self.env.company.partner_id.tz or 'UTC'
                user_timezone = timezone(user_tz)                
                current_datetime = datetime.now(user_timezone)
                current_time = current_datetime.time()
                today = current_datetime.date()
                time_430_am = time(4, 30)
                buffer_days = int(self.env['ir.config_parameter'].sudo().get_param('diet.start_date_edit_buffer', default=0))
                if current_time > time_430_am:
                    date = today + relativedelta(days=buffer_days)
                else:
                    date = today + relativedelta(days=2)
                date_str = date.strftime("%Y-%m-%d")
                options_str = (
                    xml_fields[0].get("options", "{}")
                    .replace("{", "{'min_date': '%s'" % date_str))
                xml_fields[0].set("options", options_str)
            res["arch"] = etree.tostring(eview)
        return res

    @api.depends('price', 'additional_price')
    def _compute_total(self):
        for record in self:
            record.total = record.price + record.additional_price

    @api.depends('start_date', 'additional_days', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    def _compute_end_date(self):
        for record in self:
            remaining_meal_calendar_dates = self.subscription_id.meal_calendar_ids.filtered(lambda x: x.date >= self.start_date and 
                                                    x.state in ['active_with_meal', 'freezed', 'active']).mapped('date')
            remaining_meal_calendar_dates = list(set(remaining_meal_calendar_dates))
            remaining_days = len(remaining_meal_calendar_dates)
            if not remaining_days and record.subscription_id.state == 'paid':
                remaining_days = record.subscription_id.total_days
            start_date_weekday = record.start_date.weekday()

            # List of weekdays (0: Monday, 1: Tuesday, ..., 6: Sunday)
            record_days = [
                record.monday, record.tuesday, record.wednesday, 
                record.thursday, record.friday, record.saturday, 
                record.sunday
            ]

            # Calculate excluded weekdays
            excluded_weekdays = [i for i, day in enumerate(record_days) if not day]

            # Adjust days to skip excluded weekdays
            date = record.adjust_days(record.start_date, excluded_weekdays)
            for i in range(remaining_days - 1):
                end_date = date + timedelta(days=1)
                end_date = record.adjust_days(end_date, excluded_weekdays)
                date = end_date
            end_date = date


            # Add additional days, skipping excluded weekdays
            if record.additional_days:
                added_days = record.additional_days
                while added_days > 0:
                    end_date += timedelta(days=1)
                    if end_date.weekday() not in excluded_weekdays:
                        added_days -= 1
            record.subscription_id.check_subscription_overlap(record.subscription_id.actual_start_date, end_date, record.subscription_id.partner_id)
            record.end_date = end_date

    def adjust_days(self, date, excluded_weekdays):
        flag = True
        while flag:
            if date.weekday() in excluded_weekdays:
                date += timedelta(days=1)
            else:
                flag = False
        return date

    @api.depends('subscribed_days', 'additional_days')
    def _compute_available_days(self):
        for record in self:
            record.available_days = record.subscribed_days + record.additional_days

    def submit(self):
        if self.subscription_id.ramdan_plan_applied or self.subscription_id.plan_id.is_ramdan_plan:
            ramdan_overlap = False
            loop_date = self.start_date
            ramdan_start_date = self.env.company.ramdan_start_date
            ramdan_end_date = self.env.company.ramdan_end_date
            while loop_date <= self.end_date:
                if ramdan_start_date and ramdan_end_date and ramdan_start_date <= loop_date <= ramdan_end_date:
                    ramdan_overlap = True
                    break
                loop_date += timedelta(days=1)

            if ramdan_overlap:
                raise ValidationError(_(f"You cannot edit this subscription as the start date is on {self.start_date.strftime('%d-%m-%Y')}.\nEither change the start date or use the Edit Ramdan Subscription button."))
        end_date = self.end_date
        if self.start_date >= self.subscription_id.end_date:
            self.start_date = self.subscription_id.end_date - timedelta(days=1)
            raise ValidationError(_("Start date should be less than subscription end date"))
        if self.start_date < fields.Date.today() + relativedelta(days=2):
            self.start_date = fields.Date.today() + relativedelta(days=2)
            raise ValidationError(_("Start date should be greater than or equal to today"))
        if self.start_date < self.subscription_id.actual_start_date:
            if fields.Date.today() + relativedelta(days=2) < self.subscription_id.actual_start_date:
                self.start_date = self.subscription_id.actual_start_date
            else:
                self.start_date = fields.Date.today() + relativedelta(days=2)
            raise ValidationError(_("Start date should be greater than or equal to subscription start date"))
        config_update_report = ""
        for line in self.subscription_edit_wizard_line_ids:
            config_update_report += f"{line.meal_category_id.name}: {line.subscription_config_line_id.additional_count} --> {line.meal_count}\n"
        customer_selected_meal_calendar_list = []
        for meal_calendar in self.subscription_id.meal_calendar_ids.filtered(lambda x: x.date >= self.start_date and x.meal_selection_by == 'customer' and x.state == 'active_with_meal'):
            vals = {
                'date': meal_calendar.date,
                'meal_category_id': meal_calendar.meal_category_id.id,
                'meal_id': meal_calendar.meal_id.id,
                'meal_selection_by': meal_calendar.meal_selection_by,
            }
            customer_selected_meal_calendar_list.append(vals)
        freezed_meal_calendar_list = []
        for meal_calendar in self.subscription_id.meal_calendar_ids.filtered(lambda x: x.date >= self.start_date and x.state == 'freezed'):
            vals = {
                'date': meal_calendar.date,
                'meal_category_id': meal_calendar.meal_category_id.id,
                'meal_id': meal_calendar.meal_id.id,
                'meal_selection_by': meal_calendar.meal_selection_by,
                'state': meal_calendar.state
            }
            freezed_meal_calendar_list.append(vals)
        self.subscription_id.meal_calendar_ids.filtered(lambda x: x.date >= self.start_date).unlink()
        self.subscription_id.write({
            'protein': self.protein,
            'carbs': self.carbohydrates,
            'sunday': self.sunday,
            'monday': self.monday,
            'tuesday': self.tuesday,
            'wednesday': self.wednesday,
            'thursday': self.thursday,
            'friday': self.friday,
            'saturday': self.saturday,
            'manual_price': self.additional_price + self.subscription_id.manual_price,
            'end_date': end_date
        })
        if self.subscription_id.ramdan_plan_id.is_ramdan_plan:
            ramdan_meal_config = self.subscription_id.meal_count_ids
        elif self.subscription_id.plan_id.is_ramdan_plan:
            ramdan_meal_config = self.subscription_id.ramdan_meal_count_ids
        else:
            ramdan_meal_config = self.subscription_id.meal_count_ids
        for line in self.subscription_edit_wizard_line_ids:
            subs_meal_line = ramdan_meal_config.filtered(lambda meal_line: meal_line.meal_category_id == line.meal_category_id and not meal_line.additional_meal)
            if subs_meal_line:
                subs_meal_line.additional_count = line.additional_count
            else:
                new_config_line = self.env['meals.count'].create({
                    "meal_category_id": line.meal_category_id.id,
                    "additional_count": line.additional_count
                })
                ramdan_meal_config += new_config_line
        for line in self.subscription_edit_wizard_additional_line_ids:
            subs_meal_line = ramdan_meal_config.filtered(lambda meal_line: meal_line.meal_category_id == line.meal_category_id and meal_line.additional_meal)
            if subs_meal_line:
                subs_meal_line.additional_count = line.meal_count
            else:
                new_config_line = self.env['meals.count'].create({
                    "meal_category_id": line.meal_category_id.id,
                    "additional_count": line.meal_count,
                    "additional_meal": True
                })
                ramdan_meal_config += new_config_line
        self.subscription_id.with_context(add_additional_charge=True)._compute_amount()
        self.subscription_id.generate_meal_calendar_by_date_range(self.start_date, end_date)
        self.subscription_id.apply_default_meals_by_date_range(self.start_date, end_date)
        self.subscription_id.apply_customer_selected_meals(customer_selected_meal_calendar_list)
        self.subscription_id.apply_freezed_meals(freezed_meal_calendar_list)
        self.subscription_id.message_post(body=_(
            f"Subscription Edited from {self.start_date} to {self.end_date}\n"\
            + f"Meal Count Edited: \n"\
            + f"\n{config_update_report}"
        ))


class SubscriptionEditWizardLine(models.TransientModel):
    _name = 'subscription.edit.wizard.line'
    _description = 'Subscription Edit Wizard Line'

    wizard_id = fields.Many2one('subscription.edit.wizard', string='Wizard')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    meal_count = fields.Integer('Meal Count')
    subscription_config_line_id = fields.Many2one('meals.count', string='Subscription Meal Config Line')
    base_meal_count = fields.Integer(string ="Base Meal Count")
    currency_id = fields.Many2one('res.currency', string='Currency', related='wizard_id.currency_id') 
    additional_price = fields.Monetary(string='Additional Price')
    additional_count = fields.Integer(string="Meal Count")

class SubscriptionEditWizardAdditionalLine(models.TransientModel):
    _name = 'subscription.edit.wizard.additional.line'
    _description = 'Subscription Edit Wizard Additional Line'

    wizard_id = fields.Many2one('subscription.edit.wizard', string='Wizard')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    meal_category_ids = fields.Many2many('meals.category', string='Meal Category', compute='_compute_meal_category_ids')
    meal_count = fields.Integer('Meal Count')
    subscription_config_line_id = fields.Many2one('meals.count', string='Subscription Meal Config Line')

    @api.depends('wizard_id.subscription_edit_wizard_line_ids', 'wizard_id.subscription_edit_wizard_line_ids.meal_category_id')
    def _compute_meal_category_ids(self):
        for record in self:
            record.meal_category_ids = record.wizard_id.subscription_edit_wizard_line_ids.mapped('meal_category_id')
    