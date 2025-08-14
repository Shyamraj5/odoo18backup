from odoo import models, fields, _
from odoo.exceptions import UserError


class CustomerZone(models.Model):
    _name = "customer.zone"
    _description = "Customer Zone"
    


    name = fields.Char(string ="Name")
    code = fields.Char(string ="Code")
    driver_ids = fields.Many2many('area.driver', string ="Drivers", compute='_compute_drivers')
    district_ids = fields.Many2many('customer.district', string='Districts', compute='_compute_districts')

    def _compute_districts(self):
        for zone in self:
            districts = self.env['customer.district'].search([
                ('zone_id','=',zone.id)
            ])
            zone.district_ids = False
            zone.district_ids = [(4, district.id) for district in districts]

    def _compute_drivers(self):
        for zone in self:
            drivers = self.env['area.driver'].search([
                ('service_zone_ids','in',[zone.id])
            ])
            zone.driver_ids = False
            zone.driver_ids = [(4, driver.id) for driver in drivers]
            
    def unlink(self):
        if not self.env.user.has_group('diet.group_administrator_delete'):
               raise UserError(_("You don't have access to delete this record."))
        return super(CustomerZone, self).unlink()
            