from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    expiration_date = fields.Datetime(compute='get_expiration_date', store=True)

    @api.depends('purchase_line_id')
    def get_expiration_date(self):
        for line in self:
            if line.purchase_line_id and line.product_id.tracking == 'lot':
                moves = line.purchase_line_id.move_ids
                lots = moves.mapped('lot_ids')
                if lots:
                    line.expiration_date = lots[0].expiration_date
                else:
                    line.expiration_date = False
            else:
                line.expiration_date = False
                

