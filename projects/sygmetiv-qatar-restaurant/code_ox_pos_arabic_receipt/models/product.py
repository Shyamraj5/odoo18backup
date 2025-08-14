from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    arabic_name = fields.Char(
        string='Arabic Name',
        compute='_compute_arabic_name',
        store=True,
        help="Arabic name of the product for display in POS receipts."
    )

    @api.depends('name', 'display_name')
    def _compute_arabic_name(self):
        for product in self:
            if product.with_context(lang='ar_001').name != product.name:
                product.arabic_name = product.with_context(lang='ar_001').name
            else:
                product.arabic_name = ''

    def _load_pos_data_fields(self, config_id):
        """ This function add new fields on the product model in pos app. """
        return [
            *super()._load_pos_data_fields(config_id),
            'arabic_name',
        ]