from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    is_bo = fields.Boolean(string='is Bussiness Owner', default=False)
    bo_code = fields.Char(string='BO Code')