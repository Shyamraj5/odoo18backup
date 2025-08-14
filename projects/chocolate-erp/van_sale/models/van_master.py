from odoo import models,fields,api

class VanMaster(models.Model):
    _name = "van.detail"

    name = fields.Char(string="Name")
    model = fields.Char(string="Model")
    reg_number = fields.Char("Register Number")
    company_id = fields.Many2one("res.company")
