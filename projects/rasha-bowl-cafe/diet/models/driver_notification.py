from odoo import models, fields,api,_
from odoo.exceptions import ValidationError, UserError
from TaqnyatSms import client
import re

import firebase_admin
from firebase_admin import messaging, credentials


class DriverNotification(models.Model):
    _name = "driver.notification"
    _description = "Driver notification Master"

    name = fields.Char('Name', default="New")
    driver_gender_filter = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('all', 'All'),
    ], string='Customer Gender Filter')
    title = fields.Char(string="Title")
    driver_ids = fields.Many2many('area.driver', string="Customer")
    message = fields.Text(string="Message")
    photo = fields.Binary(string="Photo", attachment=True)
    message_send_datetime = fields.Datetime('Date & Time', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    ], default='draft')
    notification_type = fields.Selection([('single', 'Single'), ('bulk', 'Bulk')], string="Notification Type", default='single')
    notification_category = fields.Selection([('birthday', 'Birthday'), ('welcome', 'Welcome'),('custom', 'Custom')], string="Notification Category")
    notification_line_ids = fields.One2many('driver.notification.line', 'notification_id', string="Notifications")

    def format_saudi_phone_number(self, phone_number):
        """
        Format and validate Saudi Arabian phone numbers.
        
        Args:
            phone_number (str): The phone number to format and validate
        
        Returns:
            str or None: Formatted phone number with 966 prefix if valid, None otherwise
        """
        # Remove any spaces, dashes, or other non-digit characters
        cleaned_number = re.sub(r'\D', '', phone_number)
        
        # Check different valid formats
        saudi_code_patterns = [
            r'^(966)?\d{9}$',  # 9 digits with optional country code
            r'^(966)?\d{10}$'  # 10 digits with optional country code
        ]
        
        # Validate number against patterns
        if not any(re.match(pattern, cleaned_number) for pattern in saudi_code_patterns):
            return None
        
        # If number doesn't start with 966, add it
        if not cleaned_number.startswith('966'):
            # If 10-digit number, remove leading 0
            if len(cleaned_number) == 10 and cleaned_number.startswith('0'):
                cleaned_number = cleaned_number[1:]
            
            # Ensure 9 digits and add 966 prefix
            if len(cleaned_number) == 9:
                return f'966{cleaned_number}'
        
        # If number already starts with 966, return as is
        return cleaned_number

    def send(self):
        try:
            sms_bearer_token = self.env['sms.gateway'].search([], limit=1).bearer_token
            sms_client = client(sms_bearer_token)
        except:
            sms_client = False
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        key_path = '/opt/odoo/diet-feed-saudi/diet/data/feed-firebase-adminsdk.json'
        key_path_local = '/home/codeox/odoo-projects/odoo17/diet-feed-saudi/diet/data/feed-firebase-adminsdk.json'
        key_path_test_server = '/opt/odoo17c/diet-feed-saudi/diet/data/feed-firebase-adminsdk.json'
        
        # Firebase credential initialization
        if os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
        elif os.path.exists(key_path_test_server):
            cred = credentials.Certificate(key_path_test_server)
        elif os.path.exists(key_path_local):
            cred = credentials.Certificate(key_path_local)
        else:
            raise ValidationError(_("Firebase Admin SDK key not found."))

        cred = credentials.Certificate(key_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        for notification in self:
            title = notification.title
            message = notification.message
            for driver in notification.driver_ids:
                my_title = title
                my_message = message
                device_token_ids = self.env['driver.device.token'].search([('driver_id','=',driver.id)])
                device_tokens = device_token_ids.mapped('device_token') if device_token_ids else []
                if 'EN_FIRSTNAME' in title:
                    my_title = my_title.replace('EN_FIRSTNAME', driver.name if driver.name else '')
                if 'EN_FIRSTNAME' in notification.message:
                    my_message = my_message.replace('EN_FIRSTNAME', driver.name if driver.name else '')
                notification_line = self.env['driver.notification.line'].create({
                    'notification_id': notification.id,
                    'driver_id': driver.id,
                    'title': my_title,
                    'message': my_message,
                    'image': notification.photo,
                    'state': 'sent',
                    'message_send_datetime': fields.Datetime.now()
                })
                response_dict = {}
                for device_token in device_tokens:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=my_title,
                            body=my_message,
                            image=f"{base_url}/web/image?model=driver.notification&id={notification.id}&field=photo"
                        ),
                        token=device_token,
                    )
                    response = messaging.send(message)
                    response_dict.update({
                        device_token: response
                    })
                notification_line.response = str(response_dict)
                phone = customer.mobile
                if phone:
                    phone_number = self.format_saudi_phone_number(phone)
                    if phone_number and sms_client:
                        sms_response = sms_client.sendMsg(my_message, [phone_number], 'FeedMeals')
                        notification_line.sms_response = sms_response
                    else:
                        notification_line.sms_response = "Invalid phone number"
            notification.write({
                'message_send_datetime': fields.Datetime.now(),
                'state': 'sent'
            })

    @api.model_create_multi
    def create(self, vals):
        res = super(DriverNotification, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('driver.notification.sequence')
        return res
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(DriverNotification, self).unlink()
    
class DriverNotificationLine(models.Model):
    _name = 'driver.notification.line'
    _description = 'Driver Notification Line'
    
    notification_id = fields.Many2one('driver.notification', string="Notification")
    driver_id = fields.Many2one('area.driver', string="Driver")
    title = fields.Char(string="Title")
    message = fields.Text(string="Message")
    image = fields.Binary(string="Image")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    ], default='draft')
    message_send_datetime = fields.Datetime('Date & Time', copy=False)
    response = fields.Char('Response')
