from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta


class AccountPayment(models.Model):
    _inherit = "account.payment"


    def generate_approval_route(self):
        """
        Generate approval route for receipt
        :return:
        """
        one_time_pending = 0
        for order in self:
            if not order.approval_team_id:
                continue
            if order.approver_ids:
                # reset approval route
                order.approver_ids.unlink()
            for team_approver in order.approval_team_id.approver_ids:

                # Add approver to the PO
                users_list = []
                if team_approver.team_id.approve_type == 'user':
                    users_list = team_approver.user_ids.ids
                elif team_approver.team_id.approve_type == 'job_type':
                    all_emp = self.env['hr.employee'].search([('job_id','in',team_approver.role_ids.ids)])
                    for each_role_ids in team_approver.role_ids:
                        all_job_ids = self.env['hr.employee'].search([('job_ids', 'in', each_role_ids.id)])
                        all_emp += all_job_ids
                    for each_emp in all_emp:
                        if each_emp.user_id:
                            users_list.append(each_emp.user_id.id)
                self.env["account.payment.approver"].create(
                    {
                        "team_id": team_approver.team_id.id,
                        "user_ids": [(6, 0, users_list)],
                        "role_ids": [(6, 0, team_approver.role_ids.ids)],
                        "order_id": order.id,
                        "team_approver_id": team_approver.id,
                    }
                )
                self.state = 'to_approve'
                if one_time_pending ==0:
                    one_time_pending =1
                    order.sudo().next_approver.state = "pending"
    
    @api.model
    def _get_team_id(self):
        approval_team_id = False
        payment_team = self.env["payment.team"].search([], limit=1)
        if payment_team:
            approval_team_id = payment_team.id
        return approval_team_id
    
    @api.model_create_multi
    def create(self, vals):
        result = super(AccountPayment, self).create(vals)
        today = fields.Date.context_today(self)
        year = today.year
        for each in result:
            if self.env["ir.sequence"].search([("code", "=", "account.payment.seq")], limit=1):
                end_code = self.env["ir.sequence"].next_by_code("account.payment.seq")
                each.name ="P" + each.journal_id.code + "/" + "MS3" + "/" + "%s" % (year) + "/" + str(end_code)
            if each.payment_type == 'outbound':
                # self._create_discount_journal_entries(each)
                each.generate_approval_route() 
        return result
    
    def update_payment_sequnce(self):
        account_payment = self.env['account.payment'].search([])
        
        for rec in account_payment:
            if rec.name and '/' in rec.name:
                parts = rec.name.split('/')
                if len(parts) > 1 and "MS3" not in parts[1]:
                    new_name = f"{parts[0]}/MS3/{parts[1]}/{parts[2]}"
                    
                    # Update the name with the new sequence
                    rec.name = new_name
        
    def _create_discount_journal_entries(self, each):
        """Handles the creation of journal entries if discounts are applied in payment_line_ids."""
        total_paid = each.amount_total
        total_without_discount = 0
        discount_amount = 0
        discount_account = each.discount_account_id.id
        account_id = self.env['account.account'].search([('code', '=', 'B10601')])

        if each.total_discount > 0:
            ref = "Vendor Bill:"
            if not discount_account:
                raise UserError(_("Please configure the Discount Account."))
            total_without_discount += total_paid + each.total_discount
            discount_amount += each.total_discount
            move_lines = [
                    Command.create({
                        'debit': total_paid,
                        'credit': 0,
                        'account_id': account_id.id,
                        'partner_id': each.partner_id.id,
                        "name": f"{ref}",
                    }),
                    Command.create({
                        'debit': 0,
                        'credit': total_without_discount,
                        'account_id': each.journal_id.default_account_id.id,
                        'partner_id': each.partner_id.id,
                        "name": f"{ref}",
                    }),
                    Command.create({
                        'debit': discount_amount,
                        'credit': 0,
                        'account_id': discount_account,
                        'partner_id': each.partner_id.id,
                        'name': f"Discount for {ref}{each.partner_id.name}",
                    })
                ]
            each.move_id.line_ids.unlink()
            each.move_id.write({'line_ids': move_lines})

        for line in each.payment_line_ids:
            if line.is_paid:
                line.invoice_id.is_paid = True
                
        #     ref = "Vendor Bill:"
        #     discount_percentage = line.discount_perc or 0
        #     if discount_percentage: 
        #         balance_amount = line.balance
        #         line_discount_amount = balance_amount * discount_percentage
        #         discount_amount += line_discount_amount
        #         total_without_discount = 0
        #         total_without_discount += total_paid + discount_amount

        # if discount_amount > 0:
        #     if not discount_account:
        #         raise UserError(_("Please select a Discount Account"))
        #     move_lines = [
        #         Command.create({
        #             'debit': total_paid,
        #             'credit': 0,
        #             'account_id': account_id.id,
        #             'partner_id': each.partner_id.id,
        #             "name": f"{ref}",
        #         }),
        #         Command.create({
        #             'debit': 0,
        #             'credit': total_without_discount,
        #             'account_id': each.journal_id.default_account_id.id,
        #             'partner_id': each.partner_id.id,
        #             "name": f"{ref}",
        #         }),
        #         Command.create({
        #             'debit': discount_amount,
        #             'credit': 0,
        #             'account_id': discount_account,
        #             'partner_id': each.partner_id.id,
        #             'name': f"Discount for Vendor:{each.partner_id.name}",
        #         })
        #     ]
        #     each.move_id.line_ids.unlink()
        #     each.move_id.write({'line_ids': move_lines})

        return True
    
    approval_team_id = fields.Many2one(
        comodel_name="payment.team",
        string="Payment Approval",
        default=_get_team_id,
        domain="[('company_id', '=', company_id)]",
    )
    po_order_approval_route = fields.Selection(string="Use Payment Approval Route",
        selection=[("no", "No"), ("optional", "Optional"), ("required", "Required")],
        default="required",
    )

    approver_ids = fields.One2many(
        comodel_name="account.payment.approver", inverse_name="order_id", string="Approvers", readonly=True
    )
    current_approver = fields.Many2one(
        comodel_name="account.payment.approver", string="Approver", compute="_compute_approver"
    )
    next_approver = fields.Many2one(
        comodel_name="account.payment.approver", string="Next Approver", compute="_compute_approver"
    )
    is_current_approver = fields.Boolean(string="Is Current Approver", compute="_compute_approver")
    first_user = fields.Boolean(string="", copy=False)
    second_user = fields.Boolean(string="", copy=False)
    thired_user = fields.Boolean(string="", copy=False)
    prepared_by = fields.Many2one("res.users", string="Prepared By", copy=False, default=lambda self: self.env.user)
    checked_by = fields.Many2one("res.users", string="Checked By", copy=False)
    approved_by = fields.Many2one("res.users", string="Approved By", copy=False)
    reviewed_by = fields.Many2one("res.users", string="Reviewed By", copy=False)
    is_user_type = fields.Boolean('Is User Type',default=False)
    is_job_type = fields.Boolean('Is Job Type',default=False)
    bi_account_move_id = fields.Many2one('account.move', string='Invoice/Bill Move')
    cancel_remarks = fields.Text(string="Reason For Reject")

    @api.onchange("approval_team_id")
    def _onchange_user_type(self):
        if self.approval_team_id.approve_type == 'job_type':
            self.is_user_type = True
        elif self.approval_team_id.approve_type == 'user':
            self.is_job_type = True

    def button_reject(self):
        for rec in self:
            if rec.state == 'to approve':
                # need to clarify what should be done here
                pass
                # if not rec.cancel_remarks:
                #     raise UserError(_("Before rejecting, please enter the Reject reasons"))
                # if rec.cancel_remarks:
                #     rec.message_post(body=_(rec.name + " has been rejected in "+ rec.state +' state' + ' and the reason is '+ rec.cancel_remarks.split(',')[-1]))
                #     rec.cancel_remarks = ''

                # rec.approver_ids.unlink()
                # rec.team_id = False
                # rec.checked_by = False
                # rec.reviewed_by = False
                # rec.approved_by = False
                # if rec.first_user:
                #     rec.first_user = False
                # if rec.second_user:
                #     rec.second_user = False
                # if rec.thired_user:
                #     rec.thired_user = False
                # rec.button_cancel()

                # if rec.requisition_id.first_user:
                #     rec.requisition_id.first_user = False
                # if rec.requisition_id.second_user:
                #     rec.requisition_id.second_user = False
                # if rec.requisition_id.thired_user:
                #     rec.requisition_id.thired_user = False
                # if rec.requisition_id.checked_by:
                #     rec.requisition_id.checked_by = False
                # if rec.requisition_id.reviewed_by:
                #     rec.requisition_id.reviewed_by = False
                # if rec.requisition_id.approved_by:
                #     rec.requisition_id.approved_by = False

                # if rec.requisition_id.approver_ids[2].state == "approved":
                #     rec.requisition_id.approver_ids[0].state = 'pending'
                #     rec.requisition_id.approver_ids[1].state = 'to approve'
                #     rec.requisition_id.approver_ids[2].state = 'to approve'
                # rec.requisition_id.write({"state": "to approve"})

              
            elif rec.state == 'pending':
                if not rec.cancel_remarks:
                    raise UserError(_("Before rejecting, please enter the Reject reasons"))
                if rec.cancel_remarks:
                    rec.message_post(body=_(rec.name + " has been rejected in "+ rec.state +' state' + ' and the reason is '+ rec.cancel_remarks.split(',')[-1]))
                    rec.cancel_remarks = ''
                if rec.first_user:
                    rec.first_user = False
                if rec.checked_by:
                    rec.checked_by = False
                if rec.approver_ids[1].state == "pending":
                    rec.approver_ids[1].state = 'to approve'
                    rec.approver_ids[0].state = 'pending'
                rec.write({"state": "to approve"})
            elif rec.state == 'authorized':
                if not rec.cancel_remarks:
                    raise UserError(_("Before rejecting, please enter the Reject reasons"))
                if rec.cancel_remarks:
                    rec.message_post(body=_(rec.name + " has been rejected in "+ rec.state +' state' + ' and the reason is '+ rec.cancel_remarks.split(',')[-1]))
                    rec.cancel_remarks = ''
                if rec.second_user:
                    rec.second_user = False
                if rec.approver_ids[2].state == "pending":
                    rec.approver_ids[2].state = 'to approve'
                    rec.approver_ids[1].state = 'pending'
                if rec.reviewed_by:
                    rec.reviewed_by = False
                rec.write({"state": "pending"})
    #    for rec in self:
    #         rec.approver_ids.unlink()
    #         rec.prepared_by = False
    #         rec.checked_by = False
    #         rec.reviewed_by = False
    #         rec.approved_by = False
    #         if rec.first_user:
    #             rec.first_user = False
    #         if rec.second_user:
    #             rec.second_user = False
    #         if rec.thired_user:
    #             rec.thired_user = False
    #         rec.write({"state": "draft"})

    @api.depends("approver_ids.state",)
    def _compute_approver(self):
        for order in self:
            if not order.approval_team_id:
                order.next_approver = False
                order.current_approver = False
                order.is_current_approver = False
                continue
            next_approvers = order.approver_ids.filtered(lambda a: a.state == "to approve")
            order.next_approver = next_approvers[0] if next_approvers else False
            current_approvers = order.approver_ids.filtered(lambda a: a.state == "pending")
            order.current_approver = current_approvers[0] if current_approvers else False
            order.is_current_approver = (
                order.approval_team_id.approve_type == 'user' and order.current_approver and self.env.user in order.current_approver.user_ids
            ) or (
                    order.approval_team_id.approve_type == 'job_type' and order.current_approver and (
                        self.env.user.employee_id.job_id and self.env.user.employee_id.job_id in order.current_approver.role_ids or self.env.user.employee_id.job_ids and set(self.env.user.employee_id.job_ids.ids).intersection(order.current_approver.role_ids.ids))
            ) or self.env.is_superuser()

    def approve_button(self):
        for order in self:
            if order.current_approver:
                # if self.env.user in order.current_approver.user_ids  or self.env.is_superuser():
                    # If current user is current approver (or superuser) update state as "approved"
                    order.current_approver.state = "approved"
                    order.message_post(body=_("Receipt approved by %s") % self.env.user.name)
                    # Check is there is another approver
                    if order.next_approver:
                        if not self.first_user:
                            self.first_user = True
                            self.checked_by = self.env.user.id
                            self.state = 'pending'
                            if self.payment_type == 'outbound':
                                company_obj = self.env['res.company'].search([("id","=",self.env.company.id)], limit="1")
                                prefix = company_obj.po_prefix
                                if not prefix:
                                    raise UserError(_("Please set PO Prefix for the selected company."))
                        elif not self.second_user:
                            self.second_user = True
                            self.reviewed_by = self.env.user.id
                            self.state = 'authorized'
                        elif not self.thired_user:
                            self.approved_by = self.env.user.id
                            self.state = 'done'
                        order.send_to_approve()

                        # order.
                    else:
                        # If there is not next approval, than assume that approval is finished and send notification
                        partner = order.user_id.partner_id if order.user_id else order.create_uid.partner_id  
                        source_ref = self.env.ref('bi_payment_approval_customisation.payment_approval')
                        order.message_mail_with_source(
                        source_ref,
                        render_values={'partner': partner.id},
                    )
                        # # Do default behaviour to set state as "purchase" and update date_approve
                        # if not self.thired_user:
                        if self.is_multi_invoice_payment == True:
                            if self.payment_line_ids:
                                line_list = []
                                account_move = self.env["account.move"].search([("id", "=", self.move_id.id)])

                                amount_total = 0
                                receivable_account = self.partner_id.property_account_receivable_id.id
                                bank_account_id = self.journal_id.default_account_id.id
                                payable_account = self.partner_id.property_account_payable_id.id
                                if self.payment_type == "inbound":
                                    line_dict = {
                                        "account_id": receivable_account,
                                        "debit": 0.0,
                                        "credit": 0.0,
                                        "amount_currency": 0.0,
                                        "currency_id": self.currency_id.id,
                                        "partner_id": self.partner_id.id,
                                    }
                                    amount_total = 0.0
                                    invoice_names = []

                                    for line in self.payment_line_ids.filtered(lambda a: a.amountpaid != 0.0):
                                        converted_amount = self.currency_id._convert(line.amountpaid, self.env.company.currency_id)
                                        line_dict["credit"] += converted_amount
                                        line_dict["amount_currency"] += line.amountpaid
                                        amount_total += line.amountpaid
                                        invoice_names.append(line.invoice_no)  

                                    invoice_name_str = ",".join(invoice_names)
                                    line_dict["name"] = f"Customer Payment: {invoice_name_str}"

                                    line_list = [
                                        (0, 0, line_dict),
                                        (0, 0, {
                                            "account_id": bank_account_id,
                                            "amount_currency": amount_total * -1,
                                            "debit": 0,
                                            "credit": amount_total,
                                            "currency_id": self.currency_id.id,
                                            "partner_id": self.partner_id.id,
                                            "name": f"Customer Payment: Total ({invoice_name_str})",
                                        }),
                                    ]
                                if self.payment_type == "outbound":
                                    line_dict = {
                                        "account_id": payable_account,
                                        "debit": 0.0,
                                        "credit": 0.0,
                                        "amount_currency": 0.0,
                                        "currency_id": self.currency_id.id,
                                        "partner_id": self.partner_id.id,
                                    }
                                    amount_total = 0.0
                                    invoice_names = []

                                    for line in self.payment_line_ids.filtered(lambda a: a.amountpaid != 0.0):
                                        converted_amount = self.currency_id._convert(line.amountpaid, self.env.company.currency_id)
                                        line_dict["debit"] += converted_amount
                                        line_dict["amount_currency"] += line.amountpaid
                                        amount_total += line.amountpaid
                                        invoice_names.append(line.invoice_no)  

                                    invoice_name_str = ",".join(invoice_names)
                                    line_dict["name"] = f"Vendor Bill: {invoice_name_str}"

                                    line_list = [
                                        (0, 0, line_dict),
                                        (0, 0, {
                                            "account_id": bank_account_id,
                                            "amount_currency": amount_total * -1,
                                            "debit": 0,
                                            "credit": amount_total,
                                            "currency_id": self.currency_id.id,
                                            "partner_id": self.partner_id.id,
                                            "name": f"Vendor Bill: Total ({invoice_name_str})",
                                        }),
                                    ]

                                    account_move.line_ids.unlink()
                                    if (order.discount_amount > 0 or any(line.discount_perc > 0 for line in self.payment_line_ids)):
                                        order._create_discount_journal_entries(order)
                                    else:
                                        account_move.line_ids = line_list
                                    self.write({"state": "posted"})
                                if self.payment_type == "inbound":
                                    for each in self.payment_line_ids:
                                        line_id = self.env["account.move.line"].search(
                                            [("invoice_id", "=", each.invoice_id.id), ("amount_residual", "<", 0)], limit=1
                                        )
                                        each.invoice_id.js_assign_outstanding_line(line_id.id)
                                if self.payment_type == "outbound":
                                    for each in self.payment_line_ids:
                                        payment_id = self
                                        domain = [('account_type', 'in', ('asset_receivable', 'liability_payable')), ('reconciled', '=', False)]
                                        if each.amountpaid > 0:
                                            if each.invoice_id:
                                                payment_lines = payment_id.line_ids.filtered_domain(domain)
                                                if payment_lines:
                                                    each.invoice_id.js_assign_outstanding_line(payment_lines.id)
                                            elif each.move_line_id:                                                
                                                to_reconcile = each.move_line_id
                                                for payment, lines in zip([payment_id], to_reconcile):
                                                    payment_lines = payment.line_ids.filtered_domain(domain)
                                                    for account in payment_lines.account_id:
                                                        (payment_lines + lines).filtered_domain([('account_id', '=', account.id),
                                                                                                ('reconciled', '=', False)]).reconcile()

                            self.approved_by = self.env.user
                            self.write({"state": "posted"})
                        else:
                            self.thired_user = True
                            order.with_context({'ctx_is_third_approval': True}).action_post()
                        move_line_ids = self.bi_account_move_id.line_ids
                        if self.bi_account_move_id:
                            available_lines = self.env['account.move.line']
                            valid_account_types = self.env['account.payment']._get_valid_payment_account_types()
                            for line in move_line_ids:
                                if line.move_id.state != 'posted':
                                    raise UserError(_("You can only register payment for posted journal entries."))

                                if line.account_type not in valid_account_types:
                                    continue
                                if line.currency_id:
                                    if line.currency_id.is_zero(line.amount_residual_currency):
                                        continue
                                else:
                                    if line.company_currency_id.is_zero(line.amount_residual):
                                        continue
                                available_lines |= line

                            # Check.
                            if not available_lines:
                                raise UserError(
                                    _("You can't register a payment because there is nothing left to pay on the selected journal items."))
                            if len(move_line_ids.company_id.root_id) > 1:
                                raise UserError(
                                    _("You can't create payments for entries belonging to different companies."))
                            if len(set(available_lines.mapped('account_type'))) > 1:
                                raise UserError(
                                    _("You can't register payments for journal items being either all inbound, either all outbound."))

                            domain = [
                                ('parent_state', '=', 'posted'),
                                ('account_type', 'in', self.env['account.payment']._get_valid_payment_account_types()),
                                ('reconciled', '=', False),
                            ]
                            payment_lines = self.line_ids.filtered_domain(domain)
                            for account in payment_lines.account_id:
                                (payment_lines + available_lines) \
                                    .filtered_domain(
                                    [('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()
                        # Keep lines having a residual amount to pay.
                       

                        # wizard_input_values = {
                        #     'allow_partials': True,
                        # }
                        # wizard = self.env['account.reconcile.wizard'].with_context(
                        #     active_model='account.move.line',
                        #     active_ids=order.lines_ids.ids,
                        # ).new(wizard_input_values)
                        # wizard.reconcile()

    def send_to_approve(self):
        for order in self:
            if order.state != "to approve" and not order.team_id:
                continue
            main_error_msg = _("Unable to send approval request to next approver.")
            if not order.next_approver:
                reason_msg = _("There are no approvers in the selected PO team.")
                raise UserError(_("{} {}".format(main_error_msg, reason_msg)))
            # use sudo as purchase user cannot update purchase.order.approver
            order.sudo().next_approver.state = "pending"
            # Now next approver became as current
            current_approver_partner = order.current_approver.user_ids.partner_id
            for each in current_approver_partner:
                self.message_post(body=_("Receipt Approval: %s") % (order.name,),
                author_id=each.id,
                message_type='notification',
            )
    def action_post(self):
        payment = super(AccountPayment, self).action_post()
        for order in self:
            # if order.state == 'posted':
                if order.thired_user:
                    order.thired_user = True
                    order.approved_by = self.env.user.id
                    order.state = "posted"
                    partner = order.user_id.partner_id if order.user_id else order.create_uid.partner_id
                    source_ref = self.env.ref('bi_payment_approval_customisation.payment_approval')
                    order.message_mail_with_source(
                    source_ref,
                    render_values={'partner': partner.id},
                    )
        return payment
    def bulk_order_approval_pending(self):
        no_access_rec = []
        for each_order in self:
            user_has_access = (
                each_order.approval_team_id.approve_type == 'user' and each_order.current_approver and self.env.user in each_order.current_approver.user_ids
            ) or (
                    each_order.approval_team_id.approve_type == 'job_type' and each_order.current_approver and (
                        self.env.user.employee_id.job_id and self.env.user.employee_id.job_id in each_order.current_approver.role_ids or self.env.user.employee_id.job_ids and set(self.env.user.employee_id.job_ids.ids).intersection(each_order.current_approver.role_ids.ids))
            ) or self.env.is_superuser()
            if each_order.state in ('draft','to approve') and user_has_access:
                each_order.approve_button()
            else:
                no_access_rec.append(each_order.name)
        if no_access_rec:
            orders_str = ', '.join(no_access_rec)
            raise UserError(f"You do not have the access to approve these orders: {orders_str}")
    def bulk_order_approval_authorize(self):
        no_access_rec = []
        for each_order in self:
            user_has_access = (
                each_order.approval_team_id.approve_type == 'user' and each_order.current_approver and self.env.user in each_order.current_approver.user_ids
            ) or (
                    each_order.approval_team_id.approve_type == 'job_type' and each_order.current_approver and (
                        self.env.user.employee_id.job_id and self.env.user.employee_id.job_id in each_order.current_approver.role_ids or self.env.user.employee_id.job_ids and set(self.env.user.employee_id.job_ids.ids).intersection(each_order.current_approver.role_ids.ids))
            ) or self.env.is_superuser()
            if each_order.state == 'pending' and user_has_access:
                each_order.approve_button()
            else:
                no_access_rec.append(each_order.name)
        if no_access_rec:
            orders_str = ', '.join(no_access_rec)
            raise UserError(f"You do not have the access to approve these orders: {orders_str}")
    
    def bulk_order_approval_approve(self):
        no_access_rec = []
        for each_order in self:
            user_has_access = (
                each_order.approval_team_id.approve_type == 'user' and each_order.current_approver and self.env.user in each_order.current_approver.user_ids
            ) or (
                    each_order.approval_team_id.approve_type == 'job_type' and each_order.current_approver and (
                        self.env.user.employee_id.job_id and self.env.user.employee_id.job_id in each_order.current_approver.role_ids or self.env.user.employee_id.job_ids and set(self.env.user.employee_id.job_ids.ids).intersection(each_order.current_approver.role_ids.ids))
            ) or self.env.is_superuser()
            if each_order.state == 'authorized' and user_has_access:
                each_order.approve_button()
            else:
                no_access_rec.append(each_order.name)
        if no_access_rec:
            orders_str = ', '.join(no_access_rec)
            raise UserError(f"You do not have the access to approve these orders: {orders_str}")
            
                    