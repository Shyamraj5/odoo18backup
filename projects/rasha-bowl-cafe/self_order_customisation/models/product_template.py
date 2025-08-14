from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    preparation_time = fields.Char(string='Preparation Time')
    short_description = fields.Char(string='Short Description')
    protein = fields.Float(string='Protein') 
    calorie = fields.Float(string='Calorie')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    preparation_time = fields.Char(related='product_tmpl_id.preparation_time', store=True)
    short_description = fields.Char(related='product_tmpl_id.short_description', store=True)
    protein = fields.Float(related='product_tmpl_id.protein', store=True)
    calorie = fields.Float(related='product_tmpl_id.calorie', store=True)

    @api.model
    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data += ['short_description', 'preparation_time', 'protein', 'calorie']
        return data
