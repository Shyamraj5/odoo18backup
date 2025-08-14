from odoo import models, fields

class ResCompanyTerms(models.Model):
    _name = "res.company.terms"
    _description = "Company Terms and Conditions"

    company_id = fields.Many2one("res.company", string="Company", required=True, ondelete="cascade")
    heading = fields.Char(string="Heading")
    description = fields.Text(string="Description")