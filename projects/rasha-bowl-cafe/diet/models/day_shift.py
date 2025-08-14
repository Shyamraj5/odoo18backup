from odoo import models, fields,api,_
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class CustomerShift(models.Model):
    _name = 'day.shift'
    _description = 'Customer Shift'

    customer_id = fields.Many2one('res.partner', string='Customer')
    period = fields.Selection([
        ('day_of_week','Day'),
        ('date_range','Date Range')],
        string='Period'
    )
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')],
        string='Day Of Week',
    )
    from_date = fields.Date(string='From Date',)
    to_date = fields.Date(string='To Date')
    display_name = fields.Char(string='Name',compute="_compute_display_name", store=True)
    shift_type = fields.Many2one('customer.shift',string='Shift')
    address_id = fields.Many2one('res.partner', string='Address')

    @api.onchange('to_date','from_date')
    def onchange_to_date_validation(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                if rec.to_date < rec.from_date:
                    raise UserError(_('To Date must be a date on or after From Date.'))
            elif rec.to_date:
                raise UserError(_('Please Enter From Date.'))

    def default_get(self, fields_list):
        defaults = super(CustomerShift, self).default_get(fields_list)
        default_shift = self.env['customer.shift'].search([('is_default', '=', True)], limit=1)
        defaults['shift_type'] = default_shift.id if default_shift else False
        return defaults
    
    @api.depends('day_of_week','from_date','to_date')
    def _compute_display_name(self):
            for rec in self:
                if rec.period == 'day_of_week':
                    rec.display_name = dict(rec._fields['day_of_week'].selection).get(rec.day_of_week)
                if rec.period == 'date_range':
                    if rec.from_date and rec.to_date:
                        date_from = rec.from_date.strftime("%d-%m-%Y")
                        date_to = rec.to_date.strftime("%d-%m-%Y")
                        rec.display_name = f'{date_from} To {date_to}'
        
    def add_shift_ids(self):
       return {
            'name':_('Health History'),
            'view_mode':'form',
            'view_type':'form',
            'type':'ir.actions.act_window',
            'res_model':'day.shift',
            'target':'new',
        }
class ResPartner(models.Model):
    _inherit = 'res.partner'

    shift_ids = fields.One2many('day.shift','customer_id', string='Shifts')


