from datetime import timedelta, datetime
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class UniversalPauseDays(models.Model):
    _name = 'universal.pause.days'
    _description = 'Universal Pause Days'
    _rec_name = 'name'

    name = fields.Char(string='Name', readonly=True, default=lambda self: _('New'))
    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    reason = fields.Char('Reason')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')
    ], string='State', default='draft', readonly=True)

    @api.constrains('from_date', 'to_date')
    def _constrains_dates(self):
        for record in self:
            if record.from_date and record.to_date and record.from_date > record.to_date:
                raise ValidationError(_("From Date should be less than To Date."))
            overlapping_pause_days = self.search([
                ('id', '!=', record.id),
                ('state', '=', 'confirm'),
                ('from_date', '<=', record.to_date),
                ('to_date', '>=', record.from_date)
            ])
            if overlapping_pause_days:
                raise ValidationError(_("Pause days cannot overlap with each other.\n Overlapping Pause Days: %s" % overlapping_pause_days.mapped('name')))
            

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('universal.pause.days') or _('New')
        return super(UniversalPauseDays, self).create(vals_list)
    
    def float_to_time_string(self, float_time):
        if not isinstance(float_time, (int, float)):
            raise ValueError(f"Invalid float time: {float_time}")

        hours = int(float_time)
        minutes = round((float_time - hours) * 100 * 60 / 100)  # Convert decimal part to minutes
        return f"{hours:02d}:{minutes:02d}"

    def action_confirm(self):
        settings = self.env['ir.config_parameter'].sudo()
        pause_time = settings.get_param('diet.universal_pause_time')
        if not pause_time:
            raise ValidationError("Please configure 'Pause Day Time' in Settings.")
        try:
            pause_time = float(pause_time)
        except ValueError:
            raise ValidationError("Invalid pause time format in settings. It should be in HH.MM format.")
        time_string = self.float_to_time_string((pause_time))
        today = datetime.now().date()
        nextcall_datetime = "{} {}".format(today, time_string)
        return {
            'name': 'Confirm Pause Day',
            'type': 'ir.actions.act_window',
            'res_model': 'pause.days.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_time': nextcall_datetime,
                'default_universal_pause_day_id': self.id,
                'active_id': self.id,
            }
        }
    
    @api.model
    def pause_subscription(self):
        try:
            # Refresh the cursor periodically
            self.env.cr.execute("SELECT 1")  # Keep connection alive
            
            confirmed_pause_days = self.search([('state', '=', 'confirm')])
            if not confirmed_pause_days:
                return True

            SubscriptionLine = self.env['diet.subscription.order']
            
            # Precompute all dates for all pause periods
            all_freeze_dates = set()
            pause_periods = []
            
            for pause_day in confirmed_pause_days:
                try:
                    date_range = []
                    temp_date = pause_day.from_date
                    while temp_date <= pause_day.to_date:
                        date_range.append(temp_date)
                        temp_date = (fields.Date.from_string(temp_date) + timedelta(days=1))
                    all_freeze_dates.update(date_range)
                    pause_periods.append({
                        'dates': date_range,
                        'reason': pause_day.reason or pause_day.name,
                        'from_date': pause_day.from_date,
                        'to_date': pause_day.to_date
                    })
                    self.env.cr.commit()  # Commit after each pause day processing
                except Exception as e:
                    _logger.error("Error processing pause day %s: %s", pause_day.id, str(e))
                    self.env.cr.rollback()
                    continue

            if not all_freeze_dates:
                return True
                
            domain = [
                ('actual_start_date', '<=', max(all_freeze_dates)),
                ('end_date', '>=', min(all_freeze_dates)),
                ('state', '=', 'in_progress')
            ]
            
            # Process in smaller batches with more frequent commits
            batch_size = 5  # Reduced from 100
            subscription_ids = SubscriptionLine.search(domain).ids
            
            # Filter in batches to avoid memory issues
            filtered_ids = []
            for i in range(0, len(subscription_ids), batch_size):
                batch_ids = subscription_ids[i:i+batch_size]
                subscriptions = SubscriptionLine.browse(batch_ids)
                filtered_ids.extend(subscriptions.filtered(
                    lambda s: any(calendar.state not in ['off_day', 'closed'] 
                    for calendar in s.meal_calendar_ids)
                ).ids)
                self.env.cr.commit()  # Commit after each filter batch
                
            subscription_ids = filtered_ids
            
            processed_count = 0
            total_batches = len(subscription_ids) // batch_size + (1 if len(subscription_ids) % batch_size else 0)
            
            for batch_num in range(total_batches):
                batch_start = batch_num * batch_size
                batch_ids = subscription_ids[batch_start:batch_start + batch_size]
                
                try:
                    subscriptions = SubscriptionLine.browse(batch_ids)
                    processed_subs = []
                    for pause in pause_periods:
                        # Refresh cursor every batch
                        self.env.cr.execute("SELECT 1")
                        
                        overlapping_subs = subscriptions.filtered(
                            lambda s: s.actual_start_date <= pause['to_date'] <= s.end_date or 
                            s.actual_start_date <= pause['from_date'] <= s.end_date
                        )
                        overlapping_subs = overlapping_subs.filtered(
                            lambda s: any(calendar.state not in ['off_day', 'closed'] 
                            for calendar in s.meal_calendar_ids)
                        )
                        for sub in overlapping_subs:
                            try:
                                processed_sub = False
                                for freeze_date in pause['dates']:
                                    if sub.actual_start_date <= freeze_date <= sub.end_date:
                                        try:
                                            sub.with_context(universal_pause=True, pause_reason=pause['reason']).freeze_subscription_day(freeze_date)
                                            processed_sub = True
                                        except ValidationError as e:
                                            if "Nothing to freeze" not in str(e):
                                                _logger.warning("Freeze error sub %s: %s", sub.id, str(e))
                                        except Exception as e:
                                            _logger.error("Freeze failed sub %s: %s", sub.id, str(e))
                                processed_count += 1 if processed_sub else 0
                                processed_subs.append(sub.order_number)
                                
                                # Commit after each subscription
                                self.env.cr.commit()
                                
                            except Exception as sub_error:
                                _logger.error("Sub %s error: %s", sub.id, str(sub_error))
                                self.env.cr.rollback()
                                continue
                    
                    _logger.info("Batch %s/%s complete (%s subs processed) [%s]", 
                            batch_num + 1, total_batches, processed_count, ', '.join(processed_subs))
                    
                except Exception as batch_error:
                    _logger.error("Batch %s failed: %s", batch_num + 1, str(batch_error))
                    self.env.cr.rollback()
                    continue
                    
            return True
            
        except Exception as e:
            _logger.exception("Critical error: %s", str(e))
            self.env.cr.rollback()
            return False
           
    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(UniversalPauseDays, self).unlink()

 