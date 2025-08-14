from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    be_code = fields.Char(string="BE Code")
    is_be = fields.Boolean(string="Is Business Executive", default=False)
    dob = fields.Date(string="Date of Birth")
    father_name = fields.Char(string="Father's Name")
    mother_name = fields.Char(string="Mother's Name")
    education_qualification = fields.Char(string="Education Qualification")
