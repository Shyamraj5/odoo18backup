from odoo import models, fields, api, _

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_round_off = fields.Boolean(string="Round Off", default=False)

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            "is_roundoff": self.is_round_off,
            })
        return res