from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    credit_note_account_id = fields.Many2one("account.account", string="Credit Note Account")
