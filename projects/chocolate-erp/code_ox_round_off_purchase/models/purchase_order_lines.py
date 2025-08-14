from odoo import models, fields

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_roundoff = fields.Boolean(string="Round Off", default=False)

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        res.update({
            "is_roundoff": self.is_roundoff,
            })
        return res
