from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_birth = fields.Date(string='Date of Birth')
    birthday = fields.Date(
        string='Next Birthday',
        compute='_compute_next_birthday',
        store=True,
    )
    next_birthdays = fields.Date(
        string='Next Birthday',
    )

    @api.depends('date_of_birth')
    def _compute_next_birthday(self):
        today = date.today()
        for partner in self:
            dob = partner.date_of_birth
            if dob:
                try:
                    next_birthday = dob.replace(year=today.year)
                    if next_birthday < today:
                        next_birthday = dob.replace(year=today.year + 1)
                except ValueError:
                    next_birthday = dob + relativedelta(years=(today.year + 1 - dob.year), day=28)

                partner.birthday = next_birthday

    @api.model    
    def update_next_birthday(self):
        today = date.today()
        partners = self.env['res.partner'].search([('date_of_birth', '!=', False)])
        for partner in partners:
            dob = partner.date_of_birth
            try:
                next_birthday = dob.replace(year=today.year)
                if next_birthday < today:
                    next_birthday = dob.replace(year=today.year + 1)
            except ValueError:
                next_birthday = dob + relativedelta(years=(today.year + 1 - dob.year), day=28)

            partner.next_birthdays = next_birthday

      
