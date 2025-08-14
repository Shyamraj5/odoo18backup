from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_all_approved = fields.Boolean(compute="_compute_is_all_approved", default=False)
    
    @api.model
    def _get_team_id(self):
        approval_team_id = False
        payment_team = self.env["payment.team"].search([('company_id', '=', self.env.company.id)], limit=1)
        if payment_team:
            approval_team_id = payment_team.id
        return approval_team_id
    payment_approval = fields.Many2one('payment.team', check_company=True, string='Payment Approval',default=_get_team_id)

    approval_route_ids = fields.One2many(
        'account.payment.approval', 'payment_id', string='Approval Route'
    )

    @api.depends()
    def _compute_is_all_approved(self):
        for record in self:
            record.is_all_approved = all(line.state == 'approved' for line in record.approval_route_ids)

    def _create_approval_lines(self):
        if self.payment_approval:
            new_approval_lines = []
            first_line = True
            for approver in self.payment_approval.approver_ids:
                for user in approver.user_ids:
                    new_approval_lines.append((0, 0, {
                        'user_id': user.id,
                        'state': 'pending' if first_line else 'to_approve'
                    }))
                    # Log message for approval waiting
                    self.message_post(
                        body=f"Waiting for approval from {user.name}",
                        message_type='notification',
                        subtype_xmlid='mail.mt_comment'
                    )
                    first_line = False
            self.approval_route_ids = new_approval_lines

    @api.model_create_multi
    def create(self, vals):
        record = super(AccountPayment, self).create(vals)
        record._create_approval_lines()
        return record
    
    def action_approve_line(self):
        next_line = self.approval_route_ids.filtered(lambda line: line.state not in ['approved'])[:1]
        if next_line:
            if not self._can_user_approve(next_line.user_id):
                raise UserError("You do not have permission to approve this document.")
            next_line.state = 'approved'
            self.message_post(
                body=f"{next_line.user_id.name} has approved this document.",
                message_type='notification',
                subtype_xmlid='mail.mt_comment'
            )
        else:
            raise UserError("No approval lines available to approve.")

    def action_reject_line(self):
        for record in self:
            next_line = record.approval_route_ids.filtered(lambda line: line.state not in ['approved', 'rejected'])[:1]
            if next_line:
                if not record._can_user_approve(next_line.user_id):
                    raise UserError("You do not have permission to reject this document.")
                next_line.state = 'rejected'
                record.message_post(
                    body=f"{next_line.user_id.name} has rejected this document.",
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )
            else:
                raise UserError("No approval lines available to reject.")

    def _can_user_approve(self, user_id):
        current_user_ids = self.env.user.ids
        return user_id.id in current_user_ids

class AccountPaymentApproval(models.Model):
    _name = 'account.payment.approval'
    _description = 'Account Payment Approval Route'

    payment_id = fields.Many2one('account.payment', string='Payment', ondelete='cascade')
    role_id = fields.Many2one('hr.job', string='Role/Position')
    state = fields.Selection([
        ('to_approve', 'To Approve'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='State', default='to_approve',required=True,store=True)
    user_id = fields.Many2one('res.users', string='Users')
