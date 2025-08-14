from odoo import models, fields, api

class AddReceivedAmountWizard(models.TransientModel):
    _name = "add.received.amount.wizard"
    _description = "Add Received Amount Wizard"

    referral_id = fields.Many2one('customer.referrals', string="Referral")
    amount = fields.Monetary(string="Amount", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='referral_id.currency_id')
    date = fields.Date(string="Date", default=fields.Date.context_today)
    wallet_type = fields.Many2one('wallet.amount.type', string='Wallet Type', required=True)
    remark = fields.Char(string="Remark",required=True)

    def action_add_received_amount(self):
        new_received = {
            'referral_id': self.referral_id.id,
            'wallet_type': self.wallet_type.id, 
            'amount': self.amount,
            'date': self.date,
            'remarks': self.remark
        }
        self.referral_id.received_ids = [(0, 0, new_received)]
        self.referral_id._compute_total_balance_amount()

        # return {'type': 'ir.actions.act_window_close'}  # Close the wizard
