from datetime import timedelta, time, datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, _, api
from odoo.exceptions import UserError
from lxml import etree
from pytz import timezone

class SubscriptionFreezeWizard(models.TransientModel):
    _name = 'subscription.freeze.wizard'
    _description = 'Subscription Freeze Wizard'
    
    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    freeze_date_from = fields.Date('Freeze Date From')
    freeze_date_to = fields.Date('Freeze Date To')
    mode = fields.Selection([
        ('freeze', 'Freeze'),
        ('unfreeze', 'Un-Freeze')
    ], string='Mode', default='freeze')

    subscription_ids = fields.Many2many(
        'diet.subscription.order', 
        string='Subscriptions',
        domain="[('state', '=', 'in_progress')]",
        default=lambda self: self.env['diet.subscription.order'].search([
            ('id', 'in', self._context.get('active_ids', [])),
            ('state', '=', 'in_progress')
        ])
    )

    is_bulk_freeze = fields.Boolean()

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id, view_type, **options)
        if view_type == "form":
            eview = etree.fromstring(res["arch"])
            
            company = self.env.company
            ramdan_start_date = company.ramdan_start_date
            ramdan_end_date = company.ramdan_end_date
            user_tz = self.env.context.get('tz') or self.env.company.partner_id.tz or 'UTC'
            user_timezone = timezone(user_tz)                
            current_datetime = datetime.now(user_timezone)
            current_time = current_datetime.time()
            is_friday = current_datetime.weekday()
            today_date = current_datetime.date()
            is_ramadan_period = (
                ramdan_start_date and ramdan_end_date and 
                ramdan_start_date <= today_date <= ramdan_end_date
            )
            time_430_am = time(4, 30)
            buffer_days = int(self.env['ir.config_parameter'].sudo().get_param('diet.subscription_freeze_buffer', default=0))
            def calculate_future_date():
                return today_date + relativedelta(days=buffer_days)
            freeze_from_fields = eview.xpath("//field[@name='freeze_date_from']")
            future_date = calculate_future_date()
            date_str = future_date.strftime("%Y-%m-%d")
            
            for field in freeze_from_fields:
                options_str = "{'min_date': '%s'}" % date_str    
                field.set("options", options_str)

            freeze_to_fields = eview.xpath("//field[@name='freeze_date_to']")
            if freeze_to_fields:
                options_str = "{'min_date': '%s'}" % date_str
                freeze_to_fields[0].set("options", options_str)

            res["arch"] = etree.tostring(eview)
        return res


    def button_confirm(self):
        self._onchange_freeze_date_from()
        freeze_start = self.freeze_date_from
        freeze_end = self.freeze_date_to
        
        # Filter valid subscriptions
        valid_subs = self.subscription_ids.filtered(lambda sub: 
            sub.state in ['in_progress', 'paid'] and 
            sub.actual_start_date <= self.freeze_date_from and 
            sub.end_date >= self.freeze_date_to
        )

        # Determine if it's a bulk freeze
        is_bulk_freeze = len(valid_subs) > 1
        
        # Freeze subscriptions in the bulk selection
        for subscription in valid_subs:
            current_freeze_start = freeze_start
            while current_freeze_start <= freeze_end:
                subscription.freeze_subscription_day(current_freeze_start, is_bulk_freeze=is_bulk_freeze)
                current_freeze_start += timedelta(days=1)
            subscription._compute_amount()
            subscription.message_post(body=_(
                f"Subscription freezed from {freeze_start.strftime('%d-%m-%Y')} to {freeze_end.strftime('%d-%m-%Y')} by {self.env.user.name}."
            ))

        return {'type': 'ir.actions.act_window_close'}

    def unfreeze(self):
        self.subscription_id.unfreeze_subscription_day(self.freeze_date_from)
        self.subscription_id._compute_amount()
        self.subscription_id.message_post(body=_(
            f"Subscription un-freezed on {self.freeze_date_from.strftime('%d-%m-%Y')} by {self.env.user.name}."
        ))

    def find_next_available_date(self, current_date, days_to_add):
        new_date = current_date + timedelta(days=days_to_add)
        while self.env['customer.meal.calendar'].search([
            ('date', '=', new_date),
            ('state', '=', 'freezed'),
            ('so_id', '=', self.subscription_id.id)
        ]):
            new_date += timedelta(days=1)
        return new_date




    @api.constrains('freeze_date_from','freeze_date_to')
    def check_freezed(self):
        meal_calendar_records =self.env['customer.meal.calendar'].search([
                ('date','>=',self.freeze_date_from),('date','<=',self.freeze_date_to),
                ('so_id','=',self.subscription_id.id)
            ])
        date_list =[]
        for records in meal_calendar_records:
            if records.state == 'freezed':
                    freezed_date =records.date.strftime('%d-%m-%Y')
                    if freezed_date not in date_list:
                        date_list.append(freezed_date)
        if date_list:
            date_list.sort()
            raise UserError(_(
                f"The subscription already freezed on {','.join(date_list)}."
            ))  
    
    @api.onchange(
        'freeze_date_from',
        'freeze_date_to'
    )
    def _onchange_freeze_date_from(self):
        if self.subscription_id:
            if not self.subscription_id.actual_start_date:
                raise UserError(_("Subscription does not have a start date."))
            
            if (
                self.freeze_date_from
                and (
                    self.freeze_date_from < self.subscription_id.actual_start_date
                    or self.freeze_date_from > self.subscription_id.end_date
                )
            ):
                raise UserError(_(
                    "Date not allowed.\nSubscriptions is from "
                    + self.subscription_id.actual_start_date.strftime('%d-%m-%Y')
                    + " and "
                    + self.subscription_id.end_date.strftime('%d-%m-%Y')
                    + "."
                ))
            
            if (
                self.freeze_date_to
                and (
                    self.freeze_date_to < self.subscription_id.actual_start_date
                    or self.freeze_date_to > self.subscription_id.end_date
                )
            ):
                raise UserError(_(
                    "Date not allowed.\nSubscriptions is from "
                    + self.subscription_id.actual_start_date.strftime('%d-%m-%Y')
                    + " and "
                    + self.subscription_id.end_date.strftime('%d-%m-%Y')
                    + "."
                ))
            
            if (
                self.freeze_date_from
                and self.freeze_date_to
                and self.freeze_date_from > self.freeze_date_to
            ):
                raise UserError(_(
                    "Date not allowed.\nSubscriptions is from "
                    + self.subscription_id.actual_start_date.strftime('%d-%m-%Y')
                    + " and "
                    + self.subscription_id.end_date.strftime('%d-%m-%Y')
                    + "."
                ))
            
            available_freeze_start_date_min = fields.Date.today() + timedelta(days=2)
            if (
                self.freeze_date_from
                and self.freeze_date_from < available_freeze_start_date_min
            ):
                raise UserError(_(
                    f"Plan can only be freezed from {available_freeze_start_date_min.strftime('%d-%m-%Y')}"
                ))
            
            if (
                self.freeze_date_from
                and self.freeze_date_to
                and (self.freeze_date_to - self.freeze_date_from).days > 30
            ):
                raise UserError(_(
                    "You can only freeze for maximum 30 days."
                ))