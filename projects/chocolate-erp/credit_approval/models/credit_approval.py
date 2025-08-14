from odoo import fields, models


class CreditApproval(models.Model):
    _name = "credit.approval"
    _description = 'Credit Approval'

    move_id = fields.Many2one("account.move", string="Invoice")
    user_id = fields.Many2one(related="move_id.invoice_user_id", string="Saleperson")
    customer_id = fields.Many2one(related="move_id.partner_id", string="Customer")
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled')
        ], string="Status", default='draft',
    )
    create_date = fields.Datetime(string='Date', default=fields.Date.today())
    approval_date = fields.Datetime(string='Approval Date')


    def approve(self):
        for rec in self:
            rec.approval_date = fields.Datetime.now()
            rec.state = 'approved'