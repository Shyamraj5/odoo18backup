from odoo import models, fields,api
from datetime import timedelta

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    _description = 'Ir Attachment'
    
    is_meal_sticker_report_file = fields.Boolean('Is Meal Sticker Report File')
    is_delivery_report_file = fields.Boolean('Is Delivery Report File')
    
    @api.autovacuum
    def _delete_meal_sticker(self):
        date_before = fields.date.today() - timedelta(days=2)
        records_to_delete = self.env['ir.attachment'].sudo().search([('create_date', '<=', date_before),('is_meal_sticker_report_file', '=', True)])
        records_to_delete.unlink()                                                                  
        return True
    
    @api.autovacuum
    def _delete_delivery_sticker(self):
        older_dates = fields.date.today() - timedelta(days=2)
        delivery_sticker_delete =  self.env['ir.attachment'].sudo().search([('create_date', '<=', older_dates),('is_delivery_report_file', '=', True)])
        delivery_sticker_delete.unlink()
        return True