from odoo import models, fields

class RecurrencePeriod(models.Model):
    """This class is used to create new model recurrence period"""
    _name = "recurrence.period"
    _description = "Recurrence Period "
    
    name = fields.Char(string="Name")
    duration = fields.Float(string="Duration")
    unit = fields.Selection([('hours', 'hours'),
                                     ('days', 'Days'),('weeks', ' Weeks'),('months', 'Months'),('years', 'Years')],
                                   string= 'Unit' )
    

class SubPackages(models.Model):
    """ This function is used to inherit subscription packages"""
    _inherit = 'subscription.package'

    recurrence_period_id = fields.Many2one("recurrence.period" , string= "Recurrence Period")