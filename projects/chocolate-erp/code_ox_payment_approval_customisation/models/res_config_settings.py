from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    po_order_approval_route = fields.Selection(string="Use Payment Approval Route",
        selection=[("no", "No"), ("optional", "Optional"), ("required", "Required")],
        default="required",
    )
