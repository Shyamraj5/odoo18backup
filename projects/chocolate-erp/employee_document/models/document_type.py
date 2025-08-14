from odoo import models, fields

class DocumentType(models.Model):
    _name = 'document.type'
    _description = 'Document Type'

    name = fields.Char(string="Document Type", required=True)
    alert = fields.Integer(string="Alert (Days)", required=True)