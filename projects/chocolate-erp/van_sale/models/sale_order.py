from odoo import api,fields,models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_person_trip_line_id = fields.Many2one('sales.person.trip.line',string="Sale Person Trip Line")