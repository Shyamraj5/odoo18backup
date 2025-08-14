from datetime import datetime, timedelta
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from zoneinfo import ZoneInfo
from pytz import timezone


class PauseDaysWizard(models.TransientModel):
    _name = 'pause.days.wizard'
    _description = 'Pause Days Wizard'

    time = fields.Char(string='Time', readonly=True)
    message = fields.Text(string='Message', compute='_compute_message')
    universal_pause_day_id = fields.Many2one('universal.pause.days', string='Pause Day')


    def float_to_time_string(self, float_time):
        if not isinstance(float_time, (int, float)):
            raise ValueError(f"Invalid float time: {float_time}")

        hours = int(float_time)
        minutes = round((float_time - hours) * 100 * 60 / 100)  # Convert decimal part to minutes
        return f"{hours:02d}:{minutes:02d}"

    def action_confirm(self):
        self.ensure_one()
        pause_day = self.env['universal.pause.days'].browse(self._context.get('active_id'))
        settings = self.env['ir.config_parameter'].sudo()
        pause_time = settings.get_param('diet.universal_pause_time')

        if not pause_time:
            raise ValidationError("Please configure 'Pause Day Time' in Settings.")

        try:
            pause_time = float(pause_time)
        except ValueError:
            raise ValidationError("Invalid pause time format in settings. It should be in HH.MM format.")

        # Get the user's timezone or use the company's timezone
        user_tz = self.env.context.get('tz') or self.env.company.partner_id.tz or 'UTC'
        user_timezone = timezone(user_tz)
        
        # Convert pause time to time string
        time_string = self.float_to_time_string(pause_time)

        # Get today's date in the user's timezone
        today = datetime.now(user_timezone).date()
        
        # Create a localized datetime
        local_nextcall = user_timezone.localize(datetime.strptime(f"{today} {time_string}", '%Y-%m-%d %H:%M'))
        
        # Convert to UTC and strip timezone info to create a naive datetime
        utc_nextcall = local_nextcall.astimezone(timezone('UTC')).replace(tzinfo=None)

        cron_job = self.env.ref('diet.ir_cron_pause_subscription', raise_if_not_found=False)
        if cron_job:
            cron_job.sudo().write({
                'nextcall': utc_nextcall,  # Now a naive datetime in UTC
                'active': True,
            })
        
        self.universal_pause_day_id.write({'state': 'confirm'})
        return {'type': 'ir.actions.act_window_close'}


    @api.depends('time')
    def _compute_message(self):
        for record in self:
            record.message = "Are you sure you want to confirm the pause day at {}".format(record.time)
            