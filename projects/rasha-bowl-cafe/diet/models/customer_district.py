from odoo import models, fields, api, _

class CustomerDistrict(models.Model):
    _name = 'customer.district'
    _description = 'Customer District'
    
    name = fields.Char('Name', required=True)
    driver_ids = fields.Many2many('area.driver', string='Drivers')
    city_id = fields.Many2one('res.country.state', string='City', required=True, domain=[('active','=',True)], default=lambda self: self.env['res.country.state'].search([('active','=',True)], limit=1))
    active = fields.Boolean('Active', default=True)
    zone_id = fields.Many2one('customer.zone', string='District')
    street_ids = fields.One2many('customer.street', 'district_id', string='Streets')
    is_default = fields.Boolean('Is Default', default=False)
    color = fields.Integer('Color Index')   
    delivery_time = fields.Char(string='Delivery Time',compute='_compute_delivery_time', store=True)
    shift_id = fields.Many2one('customer.shift', string='Shift')
    morning_delivery_from = fields.Float(string="Morning Delivery From")
    morning_delivery_from_period = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')
    ], string="Time Period", default='am')
    morning_delivery_to = fields.Float(string="Morning Delivery To")
    morning_delivery_to_period = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')
    ], string="Time Period", default='am')
    evening_delivery_from = fields.Float(string="Evening Delivery From")
    evening_delivery_from_period = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')
    ], string="Time Period", default='pm')
    evening_delivery_to = fields.Float(string="Evening Delivery To")
    evening_delivery_to_period = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')
    ], string="Time Period", default='pm')


    @api.depends('shift_id', 
                'shift_id.is_default',
                'morning_delivery_from', 
                'morning_delivery_from_period', 
                'morning_delivery_to', 
                'morning_delivery_to_period', 
                'evening_delivery_from', 
                'evening_delivery_from_period', 
                'evening_delivery_to', 
                'evening_delivery_to_period')
    def _compute_delivery_time(self):
        for rec in self:
            def format_time(time_float, period):
                hours, minutes = divmod(int(time_float * 60), 60)
                return f"{hours:02}:{minutes:02} {period.upper()}"

            delivery_time = ""

            if rec.shift_id:
                if rec.shift_id.is_default:
                    if rec.evening_delivery_from and rec.evening_delivery_to:
                        evening_from = format_time(rec.evening_delivery_from, rec.evening_delivery_from_period)
                        evening_to = format_time(rec.evening_delivery_to, rec.evening_delivery_to_period)
                        delivery_time = f"{evening_from} - {evening_to}"
                else:
                    if rec.morning_delivery_from and rec.morning_delivery_to:
                        morning_from = format_time(rec.morning_delivery_from, rec.morning_delivery_from_period)
                        morning_to = format_time(rec.morning_delivery_to, rec.morning_delivery_to_period)
                        delivery_time = f"{morning_from} - {morning_to}"

            rec.delivery_time = delivery_time
