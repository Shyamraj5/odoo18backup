from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    branch_transfer_in_id = fields.Many2one(
        'branch.transfer.in',
        string="Branch Transfer In",
        help="Reference to the branch transfer in that created this picking.",
    )
    branch_transfer_out_id = fields.Many2one(
        'branch.transfer.out',
        string="Branch Transfer Out",
        help="Reference to the branch transfer out that created this picking.",
    )

    is_branch_return = fields.Boolean(
        string="Is Branch Return",
    )

    def button_validate(self):
        res = super().button_validate()
        self = self.sudo()
        if self.branch_transfer_in_id and not self.branch_transfer_in_id.branch_transfer_out_id.returned_transfer_in_id :
            for move in self.move_ids:
                for line in move.move_line_ids:         
                    if line.lot_id and not self.is_branch_return:
                        total_margin = self.branch_transfer_in_id.line_ids.filtered(lambda l: l.product_id.id == move.product_id.id).margin
                        unit_margin = line.product_uom_id._compute_price(total_margin, line.product_id.uom_id)
                        line.lot_id.write({
                            'is_branch_sale': True,
                            'source_branch_id': self.branch_transfer_in_id.branch_id.id,
                            'margin': unit_margin,
                            
                        })
        return res
    