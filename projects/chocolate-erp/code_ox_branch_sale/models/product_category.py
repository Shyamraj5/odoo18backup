from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    branch_input_account_id = fields.Many2one(
        'account.account', string="Branch Input Account",
        domain=[('deprecated', '=', False)],
        company_dependent=True
    )
    branch_output_account_id = fields.Many2one(
        'account.account', string="Branch Output Account",
        domain=[('deprecated', '=', False)],
        company_dependent=True
    )
