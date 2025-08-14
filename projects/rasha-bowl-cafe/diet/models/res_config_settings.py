from datetime import timedelta
import time
import logging

from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    order_capacity = fields.Integer(string='Order Capacity', config_parameter ='diet.order_capacity',tracking=True)
    buffer = fields.Integer(string ="Buffer", config_parameter ='diet.buffer')
    show_shop_in_app = fields.Boolean(string="Show Shop in Mobile App", config_parameter ='diet.show_shop_in_app')
    customer_support_number = fields.Char(string='Customer Care Number', config_parameter='diet.customer_support_number', help='The customer care number')
    max_weekly_spins = fields.Integer('Maximum Weekly Spins', config_parameter='diet.max_weekly_spins')
    ramdan_start_date = fields.Date('Ramdan Start Date', related='company_id.ramdan_start_date', readonly=False)
    ramdan_end_date = fields.Date('Ramdan End Date', related='company_id.ramdan_end_date', readonly=False)
    buffer_before_4_30 = fields.Integer('Buffer Time Before 4:30', config_parameter='diet.buffer_before_4_30')
    buffer_after_4_30 = fields.Integer('Buffer Time After 4:30', config_parameter='diet.buffer_after_4_30')
    is_wednesday = fields.Boolean('Is Wednesday', config_parameter='diet.is_wednesday')
    wednesday_buffer_before_4_30 = fields.Integer('Wednesday Buffer Time Before 4:30', config_parameter='diet.wednesday_buffer_before_4_30')
    wednesday_buffer_after_4_30 = fields.Integer('Wednesday Buffer Time After 4:30', config_parameter='diet.wednesday_buffer_after_4_30')
    universal_pause_time = fields.Float(string=_('Universal Pause Time'), config_parameter='diet.universal_pause_time')
    subscription_create_buffer = fields.Integer('Subscription Create Buffer', config_parameter='diet.subscription_create_buffer')
    subscription_freeze_buffer = fields.Integer('Subscription Freeze Buffer', config_parameter='diet.subscription_freeze_buffer')
    start_date_edit_buffer = fields.Integer('Start Date Edit Buffer', config_parameter='diet.start_date_edit_buffer')

    def process_subscription_ramdan(self, subscription, ramdan_start_date, ramdan_end_date):
        for record in self:
            subscription_end_date = subscription.end_date
            # delete calendar entries without delivery generated in ramdan date period
            ramdan_plan = subscription.plan_id.ramdan_plan_id
            ramdan_choice = ramdan_plan.day_choice_ids.filtered(lambda choice: choice.no_of_day == subscription.plan_choice_id.no_of_day)
            subscription.write({
                'ramdan_plan_id': ramdan_plan.id,
                'ramdan_plan_choice_id': ramdan_choice.id,
                'ramdan_plan_applied': True
            })
            subscription._onchange_ramdan_meal_count_generation()
            calendar_entries_to_delete = subscription.meal_calendar_ids.filtered(
                lambda cal: not cal.driver_order_id
                and cal.date >= ramdan_start_date
                and cal.date <= ramdan_end_date
            )
            freezed_calendar_entries = calendar_entries_to_delete.filtered(lambda cal: cal.state == 'freezed')
            entries_to_delete = calendar_entries_to_delete - freezed_calendar_entries
            delete_date_list = []
            for entry in entries_to_delete:
                if entry.date not in delete_date_list:
                    delete_date_list.append(entry.date)
            for delete_date in delete_date_list:
                delete_entries = entries_to_delete.filtered(lambda cal: cal.date == delete_date)
                delete_entries.sudo().unlink()
                entries_to_delete -= delete_entries
                subscription.generate_meal_calendar_ramdan(delete_date, delete_date)

    # button to process the subscriptions to ramdan plan whichever applicable
    def process_ramdan_plans(self):
        # check if ramdan start date and end date is set in the settings
        ramdan_start_date = self.company_id.ramdan_start_date
        ramdan_end_date = self.company_id.ramdan_end_date
        if not ramdan_start_date:
            raise UserError(_("Ramdan start date not set."))
        if not ramdan_end_date:
            raise UserError(_("Ramdan end date not set."))
        # find out the subscriptions that come in the ramdan period and have not been converted to ramdan plan
        subscriptions = self.env['diet.subscription.order'].search([
            ('end_date', '>=', ramdan_start_date),
            ('actual_start_date', '<=', ramdan_end_date),
            ('ramdan_plan_applied', '=', False),
            ('plan_id.is_ramdan_plan', '=', False),
            ('plan_id.ramdan_plan_id', '!=', False),
            ('state','=','in_progress'),
        ])
        # for testing select any subscription id and give in the below line
        # subscriptions = self.env['diet.subscription.order'].browse(11567)
        # select each subcription and process the ramdan plan switch
        max_retries = 3
        retry_delay = 5
        batch_size = 10
        total_records = len(subscriptions)
        for i in range(0, total_records, batch_size):
            subscriptions_batch = subscriptions[i:i + batch_size]
            retry_count = 0
            while retry_count < max_retries:
                try:
                    for subscription in subscriptions_batch:
                        self.process_subscription_ramdan(subscription, ramdan_start_date, ramdan_end_date)
            
                    self.env.cr.commit()
                    _logger.info(f"Processed {min(i + batch_size, total_records)}/{total_records} records")
                    break
                except Exception as e:
                    retry_count += 1
                    _logger.error(f"Error processing batch {i // batch_size + 1} (Attempt {retry_count}): {str(e)}")
                    self.env.cr.rollback()

                    if retry_count < max_retries:
                        time.sleep(retry_delay)  # Wait before retrying
                    else:
                        _logger.error(f"Failed to process batch {i // batch_size + 1} after {max_retries} attempts")
            time.sleep(1)
        self.env['ramdan.process.log'].create({
            'processed_by': self.env.user.id,
            'processed_datetime': fields.Datetime.now()
        })
        