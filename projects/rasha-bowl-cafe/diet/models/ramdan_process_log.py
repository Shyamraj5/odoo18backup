from odoo import models, fields, api, _

class RamdanProcessLog(models.Model):
    _name = 'ramdan.process.log'
    _description = 'Ramdan Process Log'

    processed_datetime = fields.Datetime('Processed Datetime', required=True, default=fields.Datetime.now)
    processed_by = fields.Many2one('res.users', string='Processed By', required=True, default=lambda self: self.env.user)
    