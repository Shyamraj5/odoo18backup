from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    credit_note_account_id = fields.Many2one("account.account", string="Credit Note Account")
