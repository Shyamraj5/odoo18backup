from odoo import models


class ProductCategory(models.Model):
    _inherit = "product.category"


    def _compute_product_count(self):
        read_group_res = self.env['product.template'].read_group([('categ_id', 'child_of', self.ids),('is_meal','=',False)], ['categ_id'], ['categ_id'])
        group_data = dict((data['categ_id'][0], data['categ_id_count']) for data in read_group_res)
        for categ in self:
            product_count = 0
            for sub_categ_id in categ.search([('id', 'child_of', categ.ids)]).ids:
                product_count += group_data.get(sub_categ_id, 0)
            categ.product_count = product_count
