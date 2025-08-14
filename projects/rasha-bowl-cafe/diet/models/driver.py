from odoo import models, fields, api, _
from odoo.osv import expression
from datetime import timedelta
from odoo.exceptions import UserError


class AreaDriver(models.Model):
    _name = "area.driver"
    _description = "Drivers of Areas"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    


    name = fields.Char(string="Name", tracking =True)
    code = fields.Char(string="Code", readonly =True, copy=False)
    gender = fields.Selection([('male','Male'),('female', 'Female'), ('other', 'Other')], string= "Gender")
    zone_id = fields.Many2one('customer.zone', string= "District", tracking =True)
    street = fields.Char(string ="Street", tracking =True)
    avenue = fields.Char(string ="Avenue",tracking =True)
    house_number = fields.Text(string ="Delivery Address", tracking =True)
    floor_number = fields.Char(string = "Floor No", tracking =True)
    apartment_no = fields.Char(string ="Apartment No", tracking =True)
    phone =fields.Char(string ="Phone", tracking =True)
    shift_ids = fields.Many2many('customer.shift', string ="Shifts", tracking =True)
    service_zone_ids = fields.Many2many('customer.zone', string ="Service Zone")
    image = fields.Binary(string ="Image", attachment=True)
    driver_app_password = fields.Char('Driver APP Password', copy=False)
    active = fields.Boolean(string="Active")
    email = fields.Char('Email')

    def change_password(self):
        return {
            "name": _("Change Driver Password"),
            "type": "ir.actions.act_window",
            "res_model": "driver.change.password.wizard",
            "context": {
                "default_driver_id": self.id,
            },
            "target": "new",
            "view_mode": "form"
        }
 
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['code'] = self.env['ir.sequence'].next_by_code('driver.sequence')
        return super(AreaDriver, self).create(vals_list)
    
    def name_get(self):
        res =[]
        for rec in self:
            res.append((rec.id, '%s-%s' % (rec.code,rec.name)))
        return res
   
    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = []
        if operator == 'ilike':
            domain = ['|',
                    ('name', 'ilike', name),
                    ('code', 'ilike', name),]
        return self._search(domain, limit=limit, order=order)
    
    def print_pdf(self):
        return self.env.ref("diet.action_individual_driver_report_pdf").report_action(self, config=False)
    
    def print_excel(self):
        data={
            "data":self.read()
        }
        return self.env.ref("diet.action_individual_driver_report_xlsx").report_action(self, data=data,config=False)
    
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(AreaDriver, self).unlink()


class CustomerMealCalendar(models.Model):
    _inherit = 'customer.meal.calendar'
    _description = 'Customer Meal Calendar'
    
    driver_order_id = fields.Many2one('driver.order', string='Driver Order')


class DriverOrders(models.Model):
    _name = 'driver.order'
    _description = 'Driver Orders'
    _order = 'date, delivery_queue_number'
    _inherit = ['mail.thread','mail.activity.mixin']
    
    driver_id = fields.Many2one('area.driver', string='Driver', tracking=True)
    date = fields.Date('Date', tracking=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('not_delivered', 'Not Delivered')
    ], string='Status', default='pending', tracking=True)
    meal_calendar_ids = fields.One2many('customer.meal.calendar', 'driver_order_id', string='Items', tracking=True)
    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    customer_id = fields.Many2one('res.partner', string='Customer',     tracking=True)
    address_id = fields.Many2one('res.partner', string='Address')    
    city_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
        related='address_id.state_id'
    )
    district_id = fields.Many2one(
        comodel_name="customer.district",
        string="Zone",
        related='address_id.district_id'
    )
    zone_id = fields.Many2one(
        comodel_name="customer.zone",
        string="District",
        related='district_id.zone_id'
    )
    street = fields.Char(
        string="Street",
        related="address_id.street"
    )
    jedha = fields.Char(
        string="Jedha",
        related="address_id.jedha"
    )
    house_number = fields.Text(
        string="Delivery Address",
        related="address_id.house_number"
    )
    floor_number = fields.Char(
        string="Floor Number",
        related="address_id.floor_number"
    )
    shift_id = fields.Many2one(
        string="Shift",
        comodel_name="customer.shift"
    )
    comments = fields.Text(
        string="Comments",
        related="address_id.comments"
    )
    driver_comments = fields.Text('Driver Comments')
    delivery_queue_number = fields.Integer('Delivery Queue Number')
    driver_order_name = fields.Char('Delivery Order Name', compute='_compute_driver_order_name', store=True)
    eshop_order_id = fields.Many2one('diet.eshop.sale', string='Eshop Order')
    eshop_order_line_ids = fields.One2many('diet.eshop.sale.line', 'driver_order_id', string='Eshop Order Lines')
    partner_id = fields.Char(related='customer_id.customer_sequence_no', string='Customer ID')
    customer_contact = fields.Char(related='customer_id.phone', string='Customer Contact')

    @api.depends('date', 'delivery_queue_number')
    def _compute_driver_order_name(self):
        for rec in self:
            rec.driver_order_name = f'{rec.date.strftime("%d-%m-%Y")} - {rec.delivery_queue_number}'

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if operator == 'ilike' or (name or '').strip():
            # ignore 'ilike' with name containing only spaces
            domain = expression.AND([[('driver_order_name', operator, name)], domain])
        return self._search(domain, limit=limit, order=order)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.date.strftime("%d-%m-%Y")} - {rec.delivery_queue_number}'

    def delivered(self):
        for order in self:
            order.status = 'delivered'
            for calendar in order.meal_calendar_ids:
                calendar.delivery_status = 'delivered'

    def not_delivered(self):
        for order in self:
            order.status = 'not_delivered'
            for calendar in order.meal_calendar_ids:
                calendar.delivery_status = 'not_delivered'

    def open_driver_change_wizard(self):
        return {
            "name": _("Change Driver"),
            "type": "ir.actions.act_window",
            "res_model": "driver.change.wizard",
            "context": {
                "default_driver_order_ids": self.ids,
            },
            "target": "new",
            "view_mode": "form"
        }
   
                
class DriverDeviceToken(models.Model):
    _name = 'driver.device.token'
    _description = 'Driver Device Token'
    
    driver_id = fields.Many2one('area.driver', string='Driver')
    device_token = fields.Char('Device Token')
