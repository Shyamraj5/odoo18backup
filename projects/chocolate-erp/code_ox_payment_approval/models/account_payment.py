from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    state = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('approved', "Approved"),
            ('in_process', "In Process"),
            ('paid', "Paid"),
            ('canceled', "Canceled"),
            ('rejected', "Rejected"),
        ],
        required=True,
        default='draft',
        compute='_compute_state', store=True, readonly=False,
        copy=False,
    )

    def approve_payment(self):
        self.state = 'approved'

    @api.constrains('state', 'move_id')
    def _check_move_id(self):
        for payment in self:
            if (
                payment.state not in ('draft', 'canceled', 'approved')
                and not payment.move_id
                and payment.outstanding_account_id
            ):
                raise ValidationError(_("A payment with an outstanding account cannot be confirmed without having a journal entry."))

    
    

    