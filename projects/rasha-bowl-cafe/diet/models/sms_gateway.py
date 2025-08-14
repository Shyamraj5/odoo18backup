from odoo import models, fields

class SMSGateway(models.Model):
    _name = 'sms.gateway'
    _description = 'SMS Gateway'
    
    name = fields.Char('Name')
    bearer_token = fields.Char('Bearer Token')

class SmsOtpVerification(models.Model):
    _name = 'sms.otp.verification'
    _description = 'Sms Otp Verification'
    
    mobile = fields.Char('Mobile')
    otp = fields.Char('OTP')