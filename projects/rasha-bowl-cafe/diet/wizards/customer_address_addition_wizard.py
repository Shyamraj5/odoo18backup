from odoo import models, fields,api


class CustomerAddressAdditionWizard(models.Model):
    _name = "customer.address.addition.wizard"
    _description = "Customer address addition wizard"

    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    name = fields.Char(string="Nickname")
    zone_id = fields.Many2one(comodel_name="customer.zone", string="District", compute="_compute_zone_id", store=True)
    street = fields.Char(string="Street")
    house_number = fields.Text(string="Delivery Address")
    floor_number = fields.Char(string="Landmark")
    apartment_no = fields.Char(string ="Flat Number")
    district_id = fields.Many2one(comodel_name="customer.district", string="Zone", default=lambda self: self.env['customer.district'].search([('is_default','=',True)], limit=1))
    country_id = fields.Many2one(comodel_name="res.country", string="Country")
    partner_latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    city_id = fields.Many2one(comodel_name="res.country.state", string="State")
    zip = fields.Integer(string="Postal Code")
    shift_id = fields.Many2one(comodel_name="customer.shift", string="Shift",default=lambda self: self._default_shift())
    delivery_time = fields.Char('Delivery Time')
    comments = fields.Text(string="Comments")
    is_edit = fields.Boolean(string="Is Edit")
    is_default_address = fields.Boolean('Is Default Address')
    route = fields.Many2one(comodel_name="customer.street", string="Routes")

    @api.depends('district_id')
    def _compute_zone_id(self):
        for rec in self:
            if rec.district_id:
                rec.zone_id = rec.district_id.zone_id

    @api.onchange('district_id')
    def _onchange_district(self):
        if self.district_id and self.district_id.city_id:
            self.city_id = self.district_id.city_id.id
        if self.district_id and self.district_id.delivery_time:
            self.delivery_time = self.district_id.delivery_time
        if self.district_id and self.district_id.shift_id:
            self.shift_id = self.district_id.shift_id.id

    @api.onchange('shift_id')
    def _onchange_shift(self):
        if self.shift_id:
            self.customer_id.customer_address_shift_id = self.district_id.shift_id.id

    def add(self):
        self.customer_id.write({
            "child_ids": [(0,0, {
                "name": self.name,
                "zone_id": self.zone_id.id if self.zone_id else False,
                "route": self.route.id if self.route else False,
                "street": self.street if self.street else False,
                "house_number": self.house_number,
                "district_id": self.district_id.id if self.district_id else False,
                "state_id": self.city_id.id if self.city_id else False,
                "zip": self.zip,
                "floor_number": self.floor_number,
                "apartment_no":self.apartment_no,
                "shift_id": self.shift_id.id if self.shift_id else False,
                "comments": self.comments,
                "partner_latitude": self.partner_latitude,
                "partner_longitude": self.partner_longitude,
                "is_default_address":self.is_default_address if self.is_default_address else False

            })]
        })
        self.customer_id.customer_address_id = self.customer_id.child_ids[-1].id
        
    def submit(self):
            self.customer_id.write({
            "name": self.name,
            # "arabic_nickname": self.arabic_nickname,
            "zone_id": self.zone_id.id if self.zone_id else False,
            "route": self.route.id if self.route else False,
            "street": self.street if self.street else False,
            "district_id": self.district_id.id if self.district_id else False,
            "state_id": self.city_id.id if self.city_id else False,
            "house_number": self.house_number,
            "zip": self.zip,
            "floor_number": self.floor_number,
            "apartment_no":self.apartment_no,
            "shift_id": self.shift_id.id if self.shift_id else False,
            "delivery_time": self.delivery_time,
            "comments": self.comments,
            "is_default_address":self.is_default_address if self.is_default_address else False,
            "partner_latitude": self.partner_latitude,
            "partner_longitude": self.partner_longitude,
            "partner_longitude": self.customer_id.partner_longitude
        })

    def delete(self):
        self.customer_id.unlink()
    

    def _default_shift(self):
        default_shift = self.env['customer.shift'].search([('is_default', '=', 'true')], limit=1)
        return default_shift