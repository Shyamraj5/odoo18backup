from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentTeam(models.Model):
    _name = "payment.team"
    _description = "P Team"


    active = fields.Boolean("Active", default=True)
    name = fields.Char("Name", required=True)
    user_id = fields.Many2one(
        comodel_name="res.users", string="Team Leader", default=lambda self: self.env.user, required=True, index=True
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company.id,
    )

    lock_amount_total = fields.Boolean(
        string="Lock Amount Total", help="Prevent changes of amount total if approval route generated"
    )

    approver_ids = fields.One2many(
        comodel_name="payment.team.approver", inverse_name="team_id", string="Approvers",copy=True
    )
    approval_level = fields.Selection(
        string='Approval Levels',
        selection=[('1', 'One Level'), ('2', 'Two Level'),('3', 'Three Level'), ('4', 'Four Level'),('5', 'Five Level'), ('6', 'Six Level'),('7', 'Seven Level'), ('8', 'Eight Level'),('9', 'Nine Level'), ('10', 'Ten Level')],
        required=True,
        default='3'
    )
    approve_type = fields.Selection(
        string='Approve Type',
        selection=[('job_type','By Position'),('user','By User')],
        default='user'
    )
    

    @api.model_create_multi
    def create(self, vals):
        record = super().create(vals)
        if str(len(vals[0]['approver_ids']))  != vals[0]['approval_level']:
            raise UserError(_("You need to configure the appropriate approval levels"))
        return record
    def write(self, vals):
        res = super().write(vals)
        if str(len(self.approver_ids)) != self.approval_level:
            raise UserError(_("You need to configure the appropriate approval levels"))
        return res
    # @api.constrains("company_id")
    # def _check_company(self):
    #     for team in self:
    #         if team.company_id.po_order_approval_route == "no":
    #             raise UserError(_("Approval Route functionality is disabled for the company %s") % team.company_id.name)

class PaymentTeamApprover(models.Model):
    _name = "payment.team.approver"
    _description = "RE Team Approver"
    _order = "sequence"

    sequence = fields.Integer(string="Sequence", default=10)

    team_id = fields.Many2one(comodel_name="payment.team", string="Team", required=True, ondelete="cascade")

    user_ids = fields.Many2many(comodel_name="res.users", string="Approver")

    role_id = fields.Many2one(comodel_name="hr.job", string="Role/Positions",)

    role_ids = fields.Many2many(comodel_name="hr.job", string="Role/Position",)


class AccountMoveApprover(models.Model):
    _name = "account.payment.approver"
    _inherit = "payment.team.approver"
    _description = "Account Payment Approver"

    team_approver_id = fields.Many2one(
        comodel_name="payment.team.approver", string="Account Team Approver", ondelete="set null"
    )

    order_id = fields.Many2one(comodel_name="account.payment", string="Move", required=True, ondelete="cascade")

    state = fields.Selection(
        selection=[
            ("to approve", "To Approve"),
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        readonly=True,
        required=True,
        default="to approve",
    )
