from odoo import models, fields

class DriverChangePasswordWizard(models.Model):
    _name = 'driver.change.password.wizard'
    _description = 'Driver Change Password Wizard'
    
    driver_id = fields.Many2one('area.driver', string='Driver')
    new_password = fields.Char('New Password')

    def update_password(self):
        for wizard in self:
            wizard.driver_id.write({
                "driver_app_password": wizard.new_password
            })