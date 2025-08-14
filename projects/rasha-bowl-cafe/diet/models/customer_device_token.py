from odoo import models, fields

class CustomerDeviceToken(models.Model):
    _name = 'customer.device.token'
    _description = 'Customer Device Token'
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    device_token = fields.Char('Device Token')