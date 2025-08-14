from odoo import fields, models, api


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    default_order_type_id = fields.Many2one('pos.order.type', string="Order Type")
    use_custom_kot_printing = fields.Boolean(
        string='Use Custom KOT Printing',
        default=True,
    )
    flask_endpoint_url = fields.Char(
        string='Flask Printing Endpoint URL',
        help='URL of the Flask endpoint for direct printing (e.g., http://localhost:5000/print)',
    )