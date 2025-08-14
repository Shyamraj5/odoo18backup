# -*- coding: utf-8 -*-
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo import exceptions
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import random
import string
from lxml import etree
import requests
from pytz import timezone

class Partner(models.Model):
    """Inherited res partner model"""
    _inherit = 'res.partner'

    active_subscription = fields.Boolean(string="Active Subscription",
                                         default=False)
    subscription_product_line_ids = fields.One2many(
        'subscription.package.product.line', 'res_partner_id', string='Products Line')
    customer_sequence_no = fields.Char(string ="Customer ID", copy =False)
    last_name = fields.Char(string ="Last Name", tracking=True)
    address = fields.Char(string ="Customer's Address", tracking=True)
    shift_id = fields.Many2one('customer.shift', string ="Customer's Shift", tracking=True, compute="_compute_shift_id", store=True, readonly=False)
    no_of_total_sales = fields.Integer(string = "Total No of Sale")
    note = fields.Text(string = "Note", tracking=True)
    jedha = fields.Char(string="Customer's Jedha", tracking=True)
    street = fields.Char(string="Street", tracking=True)
    avenue = fields.Char(string ="Avenue", tracking=True)
    house_number = fields.Text(string ="Delivery Address", tracking=True)
    floor_number = fields.Char(string = "Floor No", tracking=True)
    apartment_no = fields.Char(string ="Customer's Apartment No", tracking=True)
    comments = fields.Text(string ="Customer Notes", tracking=True)
    district_id = fields.Many2one('customer.district', string='Zone')
    route = fields.Many2one('customer.street', string='Route')
    delivery_time = fields.Char('Delivery Time', related='district_id.delivery_time')
    zone_id = fields.Many2one('customer.zone', string="Customer's District", tracking=True)
    gender = fields.Selection([('male','Male'),('female', 'Female')], string= "Gender", tracking=True)
    date_of_birth = fields.Date(string ="DOB", tracking=True)
    day_month = fields.Char(string='Day and Month' ,compute='_compute_day_month',store="1")
    age = fields.Integer(string ="Age", compute ='_compute_age')
    height = fields.Float(string ="Height", tracking=True)
    weight = fields.Float(string ="Weight", tracking=True)
    referral_code = fields.Char(string ="Referral Code")
    inviter_referral_code = fields.Char(string="Inviter's Referral Code")
    customer_sale_order_line_ids = fields.One2many('diet.subscription.order', 'partner_id', string ="Subscription" )
    ticket_count = fields.Integer(string ="Ticket Count")
    total_rated_count = fields.Integer(string ="Total Rated Count")
    referred_count = fields.Integer(string ="Referred Count")
    deliveries_count = fields.Integer(string ="Deliveries Count")
    meals_count = fields.Integer(string ="Meals Count")
    sms_count = fields.Integer(string ="SMS Count")
    notification_count = fields.Integer(string ="Notification Count")
    consultation_count = fields.Integer(string ="Consultation Count")
    wallet_count = fields.Integer(string ="Wallet Count")
    payment_count = fields.Integer(string ="Total Payment Count")
    pause_days_line_ids = fields.One2many('pause.days.line', 'pause_id', string ="Pause Days Line")
    language = fields.Many2one('res.lang', string ="Customer Preferred Language")
    commun_language = fields.Many2one('res.lang', string ="Communication Language")
    is_customer = fields.Boolean(string ="Customer", default =False, tracking=True)
    is_supplier = fields.Boolean(string ="Supplier", default =False, tracking=True)
    is_driver = fields.Boolean(string ="Driver", default =False, tracking=True)
    is_specialist = fields.Boolean(string ="Specialist", default =False, tracking=True)
    is_active = fields.Boolean(string ="Active Customer", default =False, tracking=True)
    delivery_schedule_line_ids = fields.One2many('delivery.schedule.line', 'delivery_id', string ="Delivery Schedule Line")
    diet_app_password = fields.Char('Diet App Password', copy=False)
    allergies = fields.Many2many('product.template', 'partner_allergy_rel', 'partner_id', 'allergy_id', string ="Allergies", domain = "[('is_ingredient', '=', True)]", tracking=True)
    delivery_instruction = fields.Text(string ="Delivery Instructions", tracking=True)
    dislikes_ids = fields.Many2many('product.template', 'partner_dislike_rel', 'partner_id', 'dislike_id', string ="Dislikes", domain = "[('is_ingredient', '=', True)]", tracking=True)
    allergy_category_ids = fields.Many2many(
        'meal.ingredient.category', 'partner_allergy_categ_rel', 'partner_id',
        'allergy_categ_id', string='Allergy Category', tracking=True)
    dislike_category_ids = fields.Many2many(
        'meal.ingredient.category', 'partner_dislike_categ_rel',
        'partner_id', 'dislike_categ_id', string='Dislike Category', tracking=True)
    phone = fields.Char(string='Contact Number', tracking=True)
    mobile = fields.Char(string='Secondary Mobile', tracking=True)
    medical_report1 = fields.Binary('Medical Report 1', tracking=True)
    medical_report2 = fields.Binary('Medical Report 2', tracking=True)
    is_default_address = fields.Boolean('Is Default Address')
    leave_at_door = fields.Boolean('Leave at door')
    subscription_extension_reason_id = fields.Many2one('subscription.extension.reason', string='Subscription Extension Reason')
    payment_type =fields.Selection([('cash','Cash'),('credit','Credit')], string ="Payment Type", tracking=True)
    profile_picture_attachment_id = fields.Many2one('ir.attachment', string='Profile Picture Attachment')
    customer_meal_rating = fields.One2many('meal.customer.rating','partner_id', string = "Meal Rating")
    dietition_appointment_history_line_ids = fields.One2many('dietitian.appointment.history', 'patient_id', string ="Dietition Appointment History Line")
    health_history_ids = fields.One2many('customer.health.history', 'partner_id', string="Health History")
    notification_count = fields.Integer(string='Notification Count', compute='_compute_notification_count')
    state_id = fields.Many2one('res.country.state', string="State", tracking=True)
    customer_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Address",
        tracking=True
    )
    customer_address_zone_id = fields.Many2one(
        comodel_name="customer.zone",
        string="District",
        related="customer_address_id.zone_id",
        tracking=True
    )
    customer_address_street = fields.Char(
        string="Street",
        related="customer_address_id.street",
        tracking=True
    )
    customer_address_jedha = fields.Char(
        string="Jedha",
        related="customer_address_id.jedha",
        tracking=True
    )
    customer_address_house_number = fields.Text(
        string="Delivery Address",
        related="customer_address_id.house_number",
        tracking=True
    )
    customer_address_floor_number = fields.Char(
        string="Landmark",
        related="customer_address_id.floor_number",
        tracking=True
    )
    customer_address_apartment_no = fields.Char(
        string="Apartment No",
        related="customer_address_id.apartment_no",
        tracking=True
    )
    customer_address_shift_id = fields.Many2one(
        string="Shift",
        comodel_name="customer.shift",
        related="customer_address_id.shift_id",        
        tracking=True
    )
    customer_address_district_id = fields.Many2one(
        string="Zone", 
        comodel_name="customer.district",
        related="customer_address_id.district_id",
        tracking=True
    )
    customer_address_country_id = fields.Many2one(
        string="Country",
        comodel_name="res.country",
        default=lambda self: self.env['res.country'].search([('code','=','IN')], limit=1)
    )

    customer_address_city_id = fields.Many2one(
        string="State", 
        comodel_name="res.country.state",
        related="customer_address_id.state_id",
        tracking=True
    )

    customer_address_route = fields.Many2one(
        string="Routes", 
        comodel_name="customer.street",
        related="customer_address_id.route",
        tracking=True
    )

    customer_address_zip = fields.Char(
        string="Postal Code", 
        related="customer_address_id.zip",
        tracking=True
    )
    customer_address_delivery_time = fields.Char(
        string="Delivery Time",
        related="customer_address_id.delivery_time",
        tracking=True
    )
    customer_address_comments = fields.Text(
        string="Comments",
        related="customer_address_id.comments",
        tracking=True
    )
    customer_address_latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        related="customer_address_id.partner_latitude",
        tracking=True
    )
    customer_address_longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        related="customer_address_id.partner_longitude",
        tracking=True
    )
    customer_priority = fields.Selection([
        ('0', '0 Star'),
        ('1', '1 Star'),
        ('2', '2 Star'),
        ('3', '3 Star'),
        ('4', '4 Star'),
        ('5', '5 Star')
    ], string='Customer Priority', compute='_compute_customer_priority', store=True)
    is_form_readonly = fields.Boolean(string="Is Form Readonly", default=False)
    source = fields.Selection([
        ('social', 'Social Media'),
        ('friends', 'Through a friend'),
        ('other', 'Others')
    ], string='Source', tracking=True)
    other_source = fields.Char('Other Source', tracking=True)
    incorrect_meals = fields.Boolean(string='Incorrect Meals',compute="_compute_meal_correction",store=True)
    full_name = fields.Char(string="Customer Name", compute="_compute_full_name", store=True)
    subscription_count = fields.Integer('Subcription Count', compute='_compute_subscription_count', store=True)
    is_birthday_today = fields.Boolean(string='Is Birthday Today')
    is_vegetarian = fields.Boolean(string="I'm Vegetarian",default=False)
    is_pregnent = fields.Boolean(string="Is She Pregnant", default=False)
    favourite_meals_ids = fields.Many2many('product.template', 'meal_fav_partner_rel', string='Favourite Meals', domain=[('is_meal', '=', True)])
    customer_goals_id = fields.Many2one('customer.goals', string="Customer Goals")

    @api.depends('district_id.shift_id')
    def _compute_shift_id(self):
        for partner in self:
            if partner.district_id and partner.district_id.shift_id:
                partner.shift_id = partner.district_id.shift_id
            else:
                partner.shift_id = False

    def check_is_birthday_today(self):
        customers = self.env['res.partner'].search([('is_customer', '=', True), 
                                                    ('parent_id', '=', False), 
                                                    ('date_of_birth', '!=', False)])
        today = fields.datetime.today().strftime('%m-%d')
        updates = []
        for record in customers:
            if record.date_of_birth.strftime('%m-%d') == today:
                updates.append((record, {'is_birthday_today': True}))
            else:
                updates.append((record, {'is_birthday_today': False}))
        for record, values in updates:
            record.write(values)
        return True

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(Partner, self).unlink()

    def float_to_time_string(self, flt):
        hours = int(flt)
        minutes = int((flt - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    

    @api.depends(
        'shift_id',
        'district_id',
        'district_id.morning_delivery_from',
        'district_id.morning_delivery_from_period',
        'district_id.morning_delivery_to',
        'district_id.morning_delivery_to_period',
        'district_id.evening_delivery_from',
        'district_id.evening_delivery_from_period',
        'district_id.evening_delivery_to',
        'district_id.evening_delivery_to_period',
       
    )
    def _compute_delivery_time(self):
        for record in self:
            delivery_time = ""
            if record.district_id:
                if record.shift_id:
                    if record.shift_id.shift.lower() == 'morning':
                        delivery_time = f"{record.float_to_time_string(record.district_id.morning_delivery_from)}{record.district_id.morning_delivery_from_period.upper()} - {record.float_to_time_string(record.district_id.morning_delivery_to)}{record.district_id.morning_delivery_to_period.upper()}"
                    elif record.shift_id.shift.lower() == 'evening':
                        delivery_time = f"{record.float_to_time_string(record.district_id.evening_delivery_from)}{record.district_id.evening_delivery_from_period.upper()} - {record.float_to_time_string(record.district_id.evening_delivery_to)}{record.district_id.evening_delivery_to_period.upper()}"
                else:
                    delivery_time = f"{record.float_to_time_string(record.district_id.evening_delivery_from)}{record.district_id.evening_delivery_from_period.upper()} - {record.float_to_time_string(record.district_id.evening_delivery_to)}{record.district_id.evening_delivery_to_period.upper()}"
            record.delivery_time = delivery_time



    def default_get(self, fields_list):
        defaults = super(Partner, self).default_get(fields_list)
        default_shift = self.env['customer.shift'].search([('is_default', '=', True)], limit=1)
        defaults['shift_id'] = default_shift.id if default_shift else False
        return defaults

    @api.depends('customer_sale_order_line_ids')
    def _compute_subscription_count(self):
        for record in self:
            record.subscription_count = len(record.customer_sale_order_line_ids)

    @api.depends('name', 'last_name')
    def _compute_full_name(self):
        for record in self:
            full_name = ""
            if record.name:
                full_name += record.name
            if record.last_name:
                full_name += " " + record.last_name
            record.full_name = full_name

    @api.depends('customer_sale_order_line_ids.meal_not_set', 'customer_sale_order_line_ids.state')
    def _compute_meal_correction(self):
        for record in self.customer_sale_order_line_ids:
            if record.state == 'in_progress':
                if record.meal_not_set == True:
                    self.incorrect_meals = True
                else:
                    self.incorrect_meals = False

    def action_edit(self):
        for customer in self:
            customer.is_form_readonly = False

    def action_save(self):        
        for customer in self:
            customer.is_form_readonly = True
            
    def add_customer_address(self):
        return {
            "name": _("Add Customer Address"),
            "type": "ir.actions.act_window",
            "res_model": "customer.address.addition.wizard",
            "context": {
                "default_customer_id": self.id
            },
            "view_mode": "form",
            "target": "new",
        }

    def edit_customer_address(self):
        return {
            "name": _("Edit Customer Address"),
            "type": "ir.actions.act_window",
            "res_model": "customer.address.addition.wizard",
            "context": {
                "default_customer_id": self.customer_address_id.id,
                "default_name": self.customer_address_id.name,
                "default_zone_id": self.customer_address_id.zone_id.id if self.customer_address_id.zone_id else False,
                "default_route": self.customer_address_id.route.id if self.customer_address_id.route else False,
                "default_street": self.customer_address_id.street if self.customer_address_id.street else False,
                "default_city_id": self.customer_address_id.state_id.id,
                "default_district_id": self.customer_address_id.district_id.id,
                "default_zip": self.customer_address_id.zip,
                "default_floor_number": self.customer_address_id.floor_number,
                "default_apartment_no": self.customer_address_id.apartment_no,
                "default_house_number": self.customer_address_id.house_number,
                "default_shift_id": self.customer_address_id.shift_id.id if self.customer_address_id.shift_id else False,
                "default_delivery_time": self.customer_address_id.delivery_time,
                "default_comments": self.customer_address_id.comments,
                "default_is_default_address":self.customer_address_id.is_default_address,
                "default_partner_latitude": self.customer_address_id.partner_latitude,
                "default_partner_longitude": self.customer_address_id.partner_longitude,
                "default_is_edit": True
            },
            "view_mode": "form",
            "target": "new",
        }
    
    def delete_customer_address(self):
        meal_calendar_ids = self.env['customer.meal.calendar'].search([
            ('partner_id','=', self.id),
            ('address_id', '=', self.customer_address_id.id)
        ])
        self.customer_address_id.unlink()
        if self.child_ids:
            previous_address_id = self.child_ids[-1].id
            if previous_address_id:
                self.customer_address_id = previous_address_id
                if meal_calendar_ids:
                    meal_calendar_ids.write({'address_id': previous_address_id})
        else:
            self.customer_address_id = False

    @api.depends('subscription_count')
    def _compute_customer_priority(self):
        query = """SELECT MAX(subscription_count) FROM res_partner"""
        self._cr.execute(query)
        max_subscription_count = self._cr.fetchone()[0]
        division_log = (max_subscription_count / 5) if max_subscription_count else 1
        for record in self:
            if (4 * division_log + 1) <= record.subscription_count <= (5 * division_log):
                record.customer_priority = '5'
            elif (3 * division_log + 1) <= record.subscription_count <= (4 * division_log):
                record.customer_priority = '4'
            elif (2 * division_log + 1) <= record.subscription_count <= (3 * division_log):
                record.customer_priority = '3'
            elif (division_log + 1) <= record.subscription_count <= (2 * division_log):
                record.customer_priority = '2'
            elif 1 <= record.subscription_count <= division_log:
                record.customer_priority = '1'
            else:
                record.customer_priority = '0'

    def send_notification(self):
        return {
            "name": _("Send Notification"),
            "res_model": "customer.notification.wizard",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "target": "new",
            "context": {'default_customer_id': self.id},
        }

    def notification(self):
        partner = self.env['res.partner'].search([])
        three_day=[]
        one_day=[]
        for rec in partner:
            for record in rec.customer_sale_order_line_ids:
                date_difference = ((record.end_date)-(date.today())).days
                if date_difference == 3:
                    three_day.append(record.partner_id.id)
                if date_difference == 1:
                    one_day.append(record.partner_id.id)
        if three_day:
            datas={
                'notification_type':'single',
                'notification_category':'custom',
                'customer_ids':three_day,
                'message':'Your Subscriptions ends in 3 days'
            }
        else:
            datas=False
        if one_day:
            data={
                'notification_type':'single',
                'notification_category':'custom',
                'customer_ids':one_day,
                'message':'Your Subscriptions ends in 1 day'
            }
        else:
            data=False
        records = self.env['customer.notification'].create([datas,data])
        return records
    
    def reset_password(self):
        return {
            "name": _("Reset password"),
            "res_model": "reset.password.wizard",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "target": "new",
            "context": {'default_customer_id': self.id},
        }

    @api.depends('date_of_birth')
    def _compute_day_month(self):
        for rec in self:
            if rec.date_of_birth:
                rec.day_month = rec.date_of_birth.strftime('%m-%d')
            else:
                rec.day_month = False

    @api.constrains('is_default_address')
    def _check_default_address_consistency(self):
        for address in self:
            if address.is_default_address:
                other_default_addresses = self.env['res.partner'].search([('parent_id','=',address.parent_id.id),('id','!=',address.id)])
                other_default_addresses.write({'is_default_address': False})

    @api.onchange('dislike_category_ids')
    def _onchange_dislike_category_ids(self):
        for partner in self:
            if partner._origin and partner._origin.dislike_category_ids:
                if len(partner.dislike_category_ids) < len(partner._origin.dislike_category_ids):
                    dislike_category_ids = partner._origin.dislike_category_ids - partner.dislike_category_ids
                    dislike_ingredients = self.env['product.template'].search([
                        ('is_ingredient','=',True),
                        ('ingredient_category_id','in',dislike_category_ids.ids)
                    ])
                    partner.dislikes_ids = [(3, dislike.id) for dislike in dislike_ingredients]
                else:
                    dislike_ingredients = self.env['product.template'].search([
                        ('is_ingredient','=',True),
                        ('ingredient_category_id','in',partner.dislike_category_ids.ids)
                    ])
                    partner.dislikes_ids = [(4, dislike.id) for dislike in dislike_ingredients]
            else:
                dislike_ingredients = self.env['product.template'].search([
                    ('is_ingredient','=',True),
                    ('ingredient_category_id','in',partner.dislike_category_ids.ids)
                ])
                partner.dislikes_ids = False
                partner.dislikes_ids = [(4, dislike.id) for dislike in dislike_ingredients]

    @api.onchange('allergy_category_ids')
    def _onchange_allergy_category_ids(self):
        for partner in self:
            if partner._origin and partner._origin.allergy_category_ids:
                if len(partner.allergy_category_ids) < len(partner._origin.allergy_category_ids):
                    allergy_category_ids = partner._origin.allergy_category_ids - partner.allergy_category_ids
                    allergy_ingredients = self.env['product.template'].search([
                        ('is_ingredient','=',True),
                        ('ingredient_category_id','in',allergy_category_ids.ids)
                    ])
                    partner.allergies = [(3, allergy.id) for allergy in allergy_ingredients]
                else:
                    allergy_ingredients = self.env['product.template'].search([
                        ('is_ingredient','=',True),
                        ('ingredient_category_id','in',partner.allergy_category_ids.ids)
                    ])
                    partner.allergies = [(4, allergy.id) for allergy in allergy_ingredients]
            else:
                allergy_ingredients = self.env['product.template'].search([
                    ('is_ingredient','=',True),
                    ('ingredient_category_id','in',partner.allergy_category_ids.ids)
                ])
                partner.allergies = False
                partner.allergies = [(4, allergy.id) for allergy in allergy_ingredients]


    @api.model_create_multi
    def create(self,vals):
        for val in vals:
            partner = False
            if not val.get('parent_id',False) and (not val.get('customer_sequence_no') or val['customer_sequence_no'] == _('New')):
                if 'is_supplier' in val and val['is_supplier'] == True:
                    val['customer_sequence_no'] = self.env['ir.sequence'].next_by_code('vendor.code') or _('New')
                elif 'is_customer' in val and val['is_customer'] == True:
                    last_customer = self.search([('is_customer','=',True), ('parent_id', '=', False)], order='customer_sequence_no desc', limit=1)
                    if last_customer:
                        last_customer_sequence = last_customer.customer_sequence_no
                        last_customer_sequence = int(last_customer_sequence)
                        val['customer_sequence_no'] = str(last_customer_sequence + 1).zfill(5)
                    else:
                        val['customer_sequence_no'] = str(1).zfill(5)
            if val:
                refferal_code_condition = True
                while refferal_code_condition:
                    code_length = 8
                    characters = string.digits + string.ascii_letters + string.digits
                    referral_code = ''.join(random.choice(characters) for i in range(code_length))
                    partner_exists = self.env["res.partner"].search([("referral_code", "=", referral_code)])
                    if not partner_exists:
                        val['referral_code'] = referral_code
                        refferal_code_condition = False
            if not val.get('category_id'):
                val['category_id'] = self.env['res.partner.category'].search([('is_default_tag','=',True)]).ids
        res = super().create(vals)
        for customer in res:
            if customer.is_customer:
                data = {
                    'notification_type': 'single',
                    'notification_category': 'welcome',
                    'customer_ids': [customer.id],
                    'message': 'Thanks for joining us!'
                }
                self.env['customer.notification'].create(data)
                if customer.child_ids:
                    customer.customer_address_id = customer.child_ids[0].id
            if customer.image_1920:
                attachment = self.env['ir.attachment'].create({
                    'name': f'res_partner_{str(customer.id)}_image_1920_copy',
                    'type': 'binary',
                    'datas': customer.image_1920,
                    'res_model': 'res.partner',
                    'res_id': customer.id,
                    'public': True
                })
                customer.profile_picture_attachment_id = attachment.id
        return res

    def write(self, vals):
        if 'image_1920' in vals:
            self.profile_picture_attachment_id.unlink()
            attachment = self.env['ir.attachment'].create({
                'name': f'res_partner_{str(self.id)}_image_1920_copy',
                'type': 'binary',
                'datas': vals['image_1920'],
                'res_model': 'res.partner',
                'res_id': self.id,
                'public': True
            })
            vals['profile_picture_attachment_id'] = attachment.id
        if 'phone' in vals:
            if not self.env.user.has_group('diet.group_customer_care'):
                raise ValidationError(_("You do not have the permission to change the mobile number."))
        return super(Partner, self).write(vals)
    

    @api.depends('date_of_birth')
    def birthday_notification(self):
        today = date.today().strftime('%m-%d')
        partners_with_birthday = self.env['res.partner'].search([('date_of_birth', 'like', today)])
        if partners_with_birthday:
            notification_record = self.env['customer.notification'].create({
                'notification_type': 'single',
                'notification_category': 'birthday',
                'customer_ids': [(4, partner.id) for partner in partners_with_birthday],
                'message': 'Happy Birthday!'
            })
            return True
        else:
            return False



    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                birth_date = rec.date_of_birth
                today = date.today()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                rec.age = age
            else:
                rec.age = 0

    @api.constrains('age')
    def _age_limit(self):
        for rec in self:
            if rec.age < 10 or rec.age > 80:
                raise ValidationError ("Age must be between 10 to 80")

    @api.constrains('mobile')
    def _check_length(self):
        for rec in self:
            if rec.mobile and len(str(rec.mobile)) != 10:
                raise ValidationError(_("Enter the correct Mobile Number"))

    @api.constrains('phone')
    def check_unique_phone(self):
        for rec in self:
            if rec.phone:
                x = self.env['res.partner'].search([('phone','=', rec.phone),('id', '!=', rec.id)]) 
                if x:
                    raise ValidationError(_("""Phone number already exist. Enter another number."""))

    @api.constrains('date_of_birth')
    def check_date_of_birth(self):
        for rec in self:
            if rec.date_of_birth and rec.date_of_birth.year >= fields.Date.today().year:
                raise ValidationError(_("The entered date of birth is not acceptable."))


    def view_notification(self):
        return {
            "name": _("Notification"),
            "res_model": "customer.notification",
            "type": "ir.actions.act_window",
            "view_mode": "list",
            "target": "current",
            "domain": [('customer_ids','=',self.id)],
        }

    @api.depends('notification_count')
    def _compute_notification_count(self):
        for record in self:
            record.notification_count = self.env['customer.notification'].search_count([
                ('customer_ids', '=', record.id),
            ])
       
    def action_referral(self):
        referral_id = self.env['customer.referrals'].search([
            ('customer_id', '=', self.id)
        ])
        if not referral_id:
            referral_id = self.env['customer.referrals'].create({'customer_id': self.id})
        return {
            "name": _("Referral Transactions"),
            "res_model": "customer.referrals",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "target": "new",
            "res_id": referral_id.id,
            "context":{"default_referral_code":self.referral_code}
        }
    
    def action_view_tickets(self):
        return
    def action_view_total_rated(self):
        return
    def action_view_referred(self):
        return
    def action_view_deliveries(self):
        return
    def action_view_meals(self):
        return
    def action_view_sms(self):
        return
    def action_view_notifications(self):
        return
    def action_view_consultation(self):
        return
    def action_view_wallet(self):
        return
    def action_view_payment(self):
        return


    def create_subscription_order(self):
        default_address = self.child_ids.filtered(lambda address: address.is_default_address)

        return {
            "name": _("Subscription Order"),
            "type": "ir.actions.act_window",
            "res_model": "diet.subscription.order",
            "target": "current",
            "view_mode": "form",
            "context" : {'default_partner_id': self.id,'default_address_id':default_address.id if default_address else False}
        }

    def regenerate_meal_calendar(self):
        prev_meal_calendar = self.env['customer.meal.calendar'].search([
            ('partner_id','=', self.id)
        ])
        prev_meal_calendar.unlink()
        subs_order = self.customer_sale_order_line_ids

        for order in subs_order:
            for line in order.meal_line_ids:
                cal_date = order.actual_start_date
                sunday_meals =line.sunday_meal_ids.ids
                monday_meals = line.monday_meal_ids.ids
                tuesday_meals =line.tuesday_meal_ids.ids
                wednesday_meals =line.wednesday_meal_ids.ids
                thursday_meals =line.thursday_meal_ids.ids
                friday_meals =line.friday_meal_ids.ids
                saturday_meals =line.saturday_meal_ids.ids
                while cal_date <= order.end_date:
                    if not sunday_meals:
                        sunday_meals =line.sunday_meal_ids.ids
                    if not monday_meals:
                        monday_meals =line.monday_meal_ids.ids
                    if not tuesday_meals:
                        tuesday_meals =line.tuesday_meal_ids.ids
                    if not wednesday_meals:
                        wednesday_meals =line.wednesday_meal_ids.ids
                    if not thursday_meals:
                        thursday_meals =line.thursday_meal_ids.ids
                    if not friday_meals:
                        friday_meals =line.friday_meal_ids.ids
                    if not saturday_meals:
                        saturday_meals =line.saturday_meal_ids.ids
                    if cal_date.weekday() == 0:
                        self.env['customer.meal.calendar'].create({
                            "date": cal_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":line.meal_category_id.id,
                            "meal_id": monday_meals[0],
                            "plan_category_id": order.plan_category_id.id
                        })
                        monday_meals.pop(0)
                    elif cal_date.weekday() == 1:
                        self.env['customer.meal.calendar'].create({
                            "date": cal_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":line.meal_category_id.id,
                            "meal_id": tuesday_meals[0],
                            "plan_category_id": order.plan_category_id.id
                        })
                        tuesday_meals.pop(0)
                    elif cal_date.weekday() == 2:
                        self.env['customer.meal.calendar'].create({
                            "date": cal_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":line.meal_category_id.id,
                            "meal_id": wednesday_meals[0],
                            "plan_category_id": order.plan_category_id.id
                        })
                        wednesday_meals.pop(0)
                    elif cal_date.weekday() == 3:
                        self.env['customer.meal.calendar'].create({
                            "date": cal_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":line.meal_category_id.id,
                            "meal_id": thursday_meals[0],
                            "plan_category_id": order.plan_category_id.id
                        })
                        thursday_meals.pop(0)
                    elif cal_date.weekday() == 4:
                        self.env['customer.meal.calendar'].create({
                            "date": cal_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":line.meal_category_id.id,
                            "meal_id": friday_meals[0],
                            "plan_category_id": order.plan_category_id.id
                        })
                        friday_meals.pop(0)
                    elif cal_date.weekday() == 5:
                        self.env['customer.meal.calendar'].create({
                            "date": cal_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":line.meal_category_id.id,
                            "meal_id": saturday_meals[0],
                            "plan_category_id": order.plan_category_id.id
                        })
                        saturday_meals.pop(0)
                    elif cal_date.weekday() == 6:
                        self.env['customer.meal.calendar'].create({
                            "date": cal_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "meal_category_id":line.meal_category_id.id,
                            "meal_id": sunday_meals[0],
                            "plan_category_id": order.plan_category_id.id
                        })
                        sunday_meals.pop(0)
                    cal_date += timedelta(days=1)

    @api.model
    def _name_search(self, name, domain=[], operator='ilike', limit=None, order=None):
        if operator == 'ilike':
            domain += [
                '|',
                '|',
                '|',
                ('name', 'ilike', name),
                ('last_name', 'ilike', name),
                ('full_name', 'ilike', name),
                ('customer_sequence_no', 'ilike', name)
            ]
            return self._search(expression.AND([domain]), limit=limit, order=order)
        return super()._name_search(name, domain=domain, operator=operator, limit=limit, order=order)

    def name_get(self):
        res = []
        for rec in self:
            if rec.customer_sequence_no:
                res.append((rec.id, '[%s] %s %s' % (rec.customer_sequence_no, rec.name, rec.last_name)))
            else:
                res.append((rec.id, '%s' % (rec.name)))
        return res
    
    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat')
    def _compute_display_name(self):
        res = super(Partner, self)._compute_display_name()
        if self.env.context.get("is_address", False):
            for partner in self:
                partner.display_name = partner.name
        else:
            for partner in self:
                partner.display_name = f'{partner.name} {partner.last_name}' if partner.last_name else partner.name
        return res
    
    def get_address_ids(self):
        return [address.id for address in self.child_ids]
    
    def get_previous_address_id(self):
        if self.customer_address_id:
            current_address_id = self.customer_address_id.id 
            address_ids = self.get_address_ids()
            current_index = address_ids.index(current_address_id)
            previous_address_id = address_ids[current_index - 1]
            self.customer_address_id = previous_address_id
    
    def get_next_address_id(self):
        if self.customer_address_id:
            current_address_id = self.customer_address_id.id 
            address_ids = self.get_address_ids()
            current_index = address_ids.index(current_address_id)
            if current_index + 1 == len(address_ids):
                next_address_id = address_ids[0]
            else:
                next_address_id = address_ids[current_index + 1]
            self.customer_address_id = next_address_id

    def action_delete_customer_related_records(self):
        self.ensure_one()
        try:
            payment_transactions = self.env['payment.transaction'].search([('partner_id','=',self.id)])
            if payment_transactions:
                payment_transactions.unlink()
            payments = self.env['account.payment'].search([('partner_id','=',self.id)])
            if payments:
                payments.action_draft()
                payments.unlink()
            invoices = self.env['account.move'].search([('partner_id','=',self.id), ('move_type','=','out_invoice')])
            if invoices:
                invoices.button_draft()
                invoices.unlink()
            sale_orders = self.env['sale.order'].search([('partner_id','=',self.id)])
            if sale_orders:
                sale_orders.with_context(disable_cancel_warning=True).action_cancel()
                sale_orders.unlink()
            meal_calendar = self.env['customer.meal.calendar'].search([('partner_id','=',self.id)])
            if meal_calendar:
                meal_calendar.unlink()
            if self.customer_sale_order_line_ids:
                self.customer_sale_order_line_ids.unlink()
            notifications = self.env['customer.notification'].search([('customer_ids','=',self.id)])
            if notifications:
                notifications.unlink()
        except Exception as e:
            raise UserError(_("Error while deleting customer and related records:\n\n%s" % e))
        

class SubscriptionMealLine(models.Model):
    _name = "subscription.meal.line"
    _description = "Subscription Meal Line"

    cus_sale_order_line_id = fields.Many2one('diet.subscription.order', string ="Customer Sale Order Line")
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    default_count = fields.Integer('Default Count')
    count = fields.Integer('Count')
    carbs = fields.Float(string ="Carbs")
    protein = fields.Float(string ="Protein")
    portion_count = fields.Float(string ="Portion", default =1)


    def write(self,vals):
        res = super(SubscriptionMealLine, self).write(vals)
        if 'carbs' in vals or 'protein' in vals:
            if  not self.env.user.has_group('diet.group_dietition'):
                raise ValidationError(_("Only Dietition can edit the Protein and Carbs values!!!"))
            else:
                return res

    def add_meal(self):
        self.count += 1

    def remove_meal(self):
        if self.count > 0:
            self.count -= 1


class PauseDaysLine(models.Model):
    _name = "pause.days.line"
    _description = "Pause days Tab"


    start_date = fields.Datetime(string ="Start Date")
    Paused_days_date = fields.Date(string ="End Date")
    assigned_by = fields.Char(string ="Assigned By")
    pause_id = fields.Many2one('res.partner', string ="Pause Days Id")

class deliverySchedule(models.Model):
    _name = "delivery.schedule.line"
    _description = "Delivery Schedule"


    week_days = fields.Selection([('sun', 'Sunday'), ('mon', 'Monday'),('tue', 'Tuesday'),
                                  ('wed', 'Wednesday'), ('thu', 'Thursday'), ('fri', 'Friday'),
                                  ('sat', 'Saturday')], string ="Week days")
    address = fields.Text(string ="Address")
    shift_id = fields.Many2one('customer.shift', string ="Shift")
    start_date = fields.Date(string ="Start Date")
    end_date = fields.Date(string ="End Date")
    delivery_id = fields.Many2one('res.partner', string ="Delivery Id")


class MedicalReports(models.Model):
    _name = "medical.report"
    _description = "Customer Medical Reports"


    date = fields.Date(string ="Date", default =date.today())
    description = fields.Char(string ="Description")
    attatchment = fields.Binary(string ="Attatchments")
    report_id = fields.Many2one('res.partner', string ="Medical Reports")



class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_order_subscription = fields.Many2one('diet.subscription.order', 'Subscription Sale Order', copy=False)

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['customer_so_line_id'] = self.sale_order_subscription.id if self.sale_order_subscription else False
        return res
    
class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    show_in_app = fields.Boolean('Show in App')
    is_default_tag = fields.Boolean('Is Default Tag',default=False)

    @api.constrains('name')
    def _constrains_name(self):
        for category in self:
            query = f"""SELECT name FROM res_partner_category WHERE id != {category.id} """
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()
            for row in result:
                if category.name.lower() == row[0]['en_US'].lower():
                    raise ValidationError("Name already exists")

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(PartnerCategory, self).unlink()