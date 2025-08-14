from odoo import models, fields


class PurchaseApproveRoute(models.Model):
    _name = "purchase.approve.route"
    _description = "Purchase Approve Route"

    purchase_id = fields.Many2one(comodel_name="purchase.order", string="Purchase Order")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Approver")
    role = fields.Char(string="Role")
    state = fields.Selection(selection=[('draft', 'Pending'), ('done', 'Approved'), ('cancel', 'Disapproved')], string='Status', default='draft')
