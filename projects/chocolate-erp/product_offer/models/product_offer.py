from odoo import models, fields

class ProductOffer(models.Model):
    _name = 'product.offer'
    _description = 'Product Offer'

    name = fields.Char(string='Offer Name', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    discount_percentage = fields.Float(string='Discount Percentage', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    active = fields.Boolean(string='Active', default=True)

    def _check_offer_validity(self):
        """ Check if the offer is still valid based on the dates. """
        for offer in self:
            if offer.start_date > fields.Date.today() or offer.end_date < fields.Date.today():
                offer.active = False
