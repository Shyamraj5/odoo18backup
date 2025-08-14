from odoo import models, fields, api

class CustomerAccountDeletionRequest(models.Model):
    _name = 'customer.account.deletion.request'
    _description = 'Customer Account Deletion Request'
    
    name = fields.Char('Name', default='New')
    customer_id = fields.Many2one('res.partner', string='Customer')
    request_datetime = fields.Datetime('Request Date', default=fields.Datetime.now())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('deleted', 'Deleted'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(CustomerAccountDeletionRequest, self).create(vals_list)
        for app in res:
            app.name = self.env['ir.sequence'].next_by_code('customer.account.deletion.sequence')
        return res