from odoo import models, fields, api

class AxceptPaymentMethod(models.Model):
    _name = 'axcept.payment.method'
    _description = "Axcept Payment Method"

    name = fields.Char(string="Name")
    
class JournalAdding(models.Model):
    _inherit = 'account.journal'

    payment_method = fields.Many2many(
        'axcept.payment.method',
        string='Axcept Payment Methods'
    )
    