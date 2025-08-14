import os
import firebase_admin
from firebase_admin import credentials, messaging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
from TaqnyatSms import client
import re

from odoo import models, fields,api,_
from odoo.exceptions import ValidationError, UserError
from odoo.http import request


class CustomerNotification(models.Model):
    _name = "customer.notification"
    _description = "Customer notification Master"

    name = fields.Char('Name', default="New")
    customer_gender_filter = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('all', 'All'),
    ], string='Customer Gender Filter')
    title = fields.Char(string="Title")
    customer_ids = fields.Many2many('res.partner', string="Customer")
    message = fields.Text(string="Message")
    photo = fields.Binary(string="Photo", attachment=True)
    message_send_datetime = fields.Datetime('Date & Time', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    ], default='draft')
    notification_type = fields.Selection([('single', 'Single'), ('bulk', 'Bulk')], string="Notification Type", default='single')
    notification_category = fields.Selection([('birthday', 'Birthday'), ('welcome', 'Welcome'),('custom', 'Custom')], string="Notification Category")
    notification_line_ids = fields.One2many('customer.notification.line', 'notification_id', string="Notifications")
    send_by_id = fields.Many2one('res.users', string='Send By')
    schedule_id = fields.Many2one('customer.notification.schedule', string='Schedule')

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

        def send_firebase_notification(device_token, my_title, my_message, notification_id, base_url, notification_line):
            try:
                message_obj = messaging.Message(
                    notification=messaging.Notification(
                        title=my_title,
                        body=my_message
                    ),
                    data={
                        "title": my_title,
                        "body": my_message,
                        "image": f"{base_url}/web/image?model=customer.notification&id={notification_id}&field=photo"
                    },
                    apns=messaging.APNSConfig(
                        headers={
                            "apns-priority": "10"  # High priority for immediate delivery
                        },
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                content_available=True,  
                                mutable_content=True    
                            )
                        ),
                    ),
                    token=device_token,
                )
                response = messaging.send(message_obj)
                notification_line.response = json.dumps({device_token: response})
            except Exception as e:
                notification_line.response = json.dumps({device_token: f"Error: {str(e)}"})

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        key_path = '/opt/odoo/diet-feed-saudi/diet/data/feed-firebase-adminsdk.json'
        key_path_local = '/home/codeox/Documents/odoo17/diet-feed-saudi/diet/data/feed-firebase-adminsdk.json'
        key_path_test_server = '/opt/odoo17c/diet-feed-saudi/diet/data/feed-firebase-adminsdk.json'

        try:
            sms_bearer_token = self.env['sms.gateway'].search([], limit=1).bearer_token
            sms_client = client(sms_bearer_token)
        except:
            sms_client = False
        
        # Firebase credential initialization
        if os.path.exists(key_path):
            cred = credentials.Certificate(key_path)
        elif os.path.exists(key_path_test_server):
            cred = credentials.Certificate(key_path_test_server)
        elif os.path.exists(key_path_local):
            cred = credentials.Certificate(key_path_local)
        else:
            raise ValidationError(_("Firebase Admin SDK key not found."))

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            
        for notification in self:
            if not notification.customer_ids and not notification.customer_gender_filter:
                raise ValidationError(_("Please select customers."))
            
            # Filtering customers based on gender
            customer_ids = notification.customer_ids
            if notification.customer_gender_filter == 'male':
                customer_ids = self.env['res.partner'].search([('is_customer', '=', True), ('gender', '=', 'male'), ('parent_id', '=', False)])
            elif notification.customer_gender_filter == 'female':
                customer_ids = self.env['res.partner'].search([('is_customer', '=', True), ('gender', '=', 'female'), ('parent_id', '=', False)])
            elif notification.customer_gender_filter == 'all':
                customer_ids = self.env['res.partner'].search([('is_customer', '=', True), ('parent_id', '=', False)])
            device_token_ids = self.env['customer.device.token'].search([('partner_id', 'in', customer_ids.ids)])
            customers_logged_in = device_token_ids.mapped('partner_id')
            
            # Initializing thread pool for parallel tasks
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for customer in customers_logged_in:
                    my_title = notification.title
                    my_message = notification.message
                    device_token_ids = self.env['customer.device.token'].search([('partner_id','=',customer.id)])
                    device_tokens = device_token_ids.mapped('device_token') if device_token_ids else []

                    # Personalize title and message
                    if 'EN_FIRSTNAME' in my_title:
                        my_title = my_title.replace('EN_FIRSTNAME', customer.name or '')
                    if 'EN_FIRSTNAME' in my_message:
                        my_message = my_message.replace('EN_FIRSTNAME', customer.name or '')
                    
                    # Create notification log
                    notification_line = self.env['customer.notification.line'].create({
                        'notification_id': notification.id,
                        'customer_id': customer.id,
                        'title': my_title,
                        'message': my_message,
                        'state': 'sent',
                        'message_send_datetime': fields.Datetime.now(),
                        'send_by_id': self.env.user.id
                    })

                    # Send Firebase notifications in parallel
                    for device_token in device_tokens:
                        futures.append(executor.submit(
                            send_firebase_notification,
                            device_token, my_title, my_message, notification.id, base_url, notification_line
                        ))

                    phone = customer.mobile
                    if phone:
                        phone_number = self.format_saudi_phone_number(phone)
                        if phone_number and sms_client:
                            sms_response = sms_client.sendMsg(my_message, [phone_number], 'DietDone')
                            notification_line.sms_response = sms_response
                        else:
                            notification_line.sms_response = "Invalid phone number"

            # Update notification state
            notification.write({
                'message_send_datetime': fields.Datetime.now(),
                'state': 'sent',
                'send_by_id': self.env.user.id
            })

    @api.model_create_multi
    def create(self, vals):
        res = super(CustomerNotification, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('customer.notification.sequence')
        return res

    def open_notification(self):
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'customer.notification',
            'res_id': self.id,
            'target': 'current',
        }
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(CustomerNotification, self).unlink()
    
class CustomerNotificationLine(models.Model):
    _name = 'customer.notification.line'
    _description = 'Customer Notification Line'
    
    notification_id = fields.Many2one('customer.notification', string="Notification")
    customer_id = fields.Many2one('res.partner', string="Customer")
    title = fields.Char(string="Title")
    message = fields.Text(string="Description")
    image = fields.Binary(string="Image")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    ], default='draft')
    message_send_datetime = fields.Datetime('Date & Time', copy=False)
    response = fields.Char('Response')
    sms_response = fields.Char('SMS Response')
    send_by_id = fields.Many2one('res.users', string='Send By')
