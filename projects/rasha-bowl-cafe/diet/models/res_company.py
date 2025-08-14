from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Res Company'

    ramdan_start_date = fields.Date('Ramdan Start Date')
    ramdan_end_date = fields.Date('Ramdan End Date')
    terms_and_conditions_ids = fields.One2many(
        "res.company.terms",
        "company_id",
        string="Terms and Conditions"
    )
