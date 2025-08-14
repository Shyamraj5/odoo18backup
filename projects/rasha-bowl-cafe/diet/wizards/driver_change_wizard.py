from odoo import models, fields, _
from odoo.exceptions import UserError

class DriverChangeWizard(models.TransientModel):
    _name = 'driver.change.wizard'
    _description = 'Driver Change Wizard'

    driver_id = fields.Many2one('area.driver', string='Driver')
    driver_order_ids = fields.Many2many('driver.order', string='Driver Orders')
    shift_id = fields.Many2one('customer.shift', string='Shift')

    def change_driver(self):
        for order in self.driver_order_ids:
            if order.status == 'delivered':
                raise UserError(_('You cannot change the driver/shift for a delivered order'))
            update_vals = {}
            if self.driver_id:
                update_vals['driver_id'] = self.driver_id.id
            if self.shift_id:
                update_vals['shift_id'] = self.shift_id.id
            order.write(update_vals)
            if self.shift_id:
                for calendar in order.meal_calendar_ids:
                    calendar.write({
                        'shift_id': self.shift_id.id,
                    })
