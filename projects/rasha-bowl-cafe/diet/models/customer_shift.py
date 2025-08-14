from odoo import models, fields, _ 
from odoo.exceptions import UserError


class CustomerShift(models.Model):
    _name = "customer.shift"
    _description = "Customer Shift"
    _rec_name = "shift"

    shift = fields.Char(string ="Shift")
    is_default = fields.Boolean(string="Is Evening Shift")
    morning_driver_id = fields.Many2one('area.driver' ,string="Morning Driver")
    evening_driver_id = fields.Many2one('area.driver' ,string="Evening Driver")
    zone_id = fields.Many2one('customer.zone', string="District")

    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(CustomerShift, self).unlink()