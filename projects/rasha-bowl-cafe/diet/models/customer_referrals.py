from odoo import models, fields,api


class CustomerReferrals(models.Model):
    _name = "customer.referrals"
    _description = "Customer Referrals Master"

    customer_id = fields.Many2one('res.partner', string="Customer Name")
    referral_code = fields.Char(string="Referral Code", related='customer_id.referral_code')
    total_received = fields.Monetary(string="Total Received", compute='_compute_totals', store=True)
    total_paid = fields.Monetary(string="Total Paid", compute='_compute_totals', store=True)
    balance_amount = fields.Monetary(string="Balance Amount", compute='_compute_total_balance_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='customer_id.currency_id')
    received_ids = fields.One2many('customer.referrals.received', 'referral_id', string="Referral")
    spend_ids = fields.One2many('customer.referrals.spend', 'referral_id', string="Amount Detail")
    total_split_ids = fields.One2many('referrals.total.split','referral_id', string="Total Split")
    reward_level_id = fields.Many2one('referral.reward.levels', string="Reward Level", compute='_compute_reward_level', store=True)

    @api.depends('received_ids.amount', 'spend_ids.amount')
    def _compute_totals(self):
        for record in self:
            total_received = 0.0
            total_paid = 0.0
            total_data = {}

            for line in record.received_ids:
                total_received += line.amount
                wallet_type = line.wallet_type
                if wallet_type in total_data:
                    total_data[wallet_type] += line.amount
                else:
                    total_data[wallet_type] = line.amount

            for line in record.spend_ids:
                total_paid += line.amount
                wallet_type = line.wallet_type
                if wallet_type in total_data:
                    total_data[wallet_type] -= line.amount
                else:
                    total_data[wallet_type] = -line.amount

            record.total_received = total_received
            record.total_paid = total_paid

            record.total_split_ids = [(5, 0, 0)] 
            total_lines = [(0, 0, {'wallet_type': wallet_type.id, 'total': total}) for wallet_type, total in total_data.items()]
            record.total_split_ids = total_lines

    @api.depends('total_received', 'total_paid')
    def _compute_total_balance_amount(self):
            for record in self:
                total = record.total_received - record.total_paid
                record.balance_amount = total

    @api.depends('balance_amount')
    def _compute_reward_level(self):
        for record in self:
            reward_level_id = self.env['referral.reward.levels'].search([('reward_amount', '<=', record.balance_amount)], order='reward_amount desc', limit=1)
            record.reward_level_id = reward_level_id.id

    def add_received_manually(self):
        return {
            'name': 'Add Received Amount',
            'type': 'ir.actions.act_window',
            'res_model': 'add.received.amount.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_referral_id' : self.id },
        }

class ReferralsTotalSplit(models.Model):
    _name = "referrals.total.split"
    _description = "Rferral Total Split"

    referral_id = fields.Many2one('customer.referrals', string="Referral")
    currency_id = fields.Many2one('res.currency', string='Currency', related='referral_id.currency_id')
    wallet_type = fields.Many2one('wallet.amount.type', string='Wallet Type')
    total = fields.Monetary(string="Amount")

class CustomerReferralsReceived(models.Model):
    _name = "customer.referrals.received"
    _description = "Customer referral Received"

    referral_id = fields.Many2one('customer.referrals', string="Referral")
    currency_id = fields.Many2one('res.currency', string='Currency', related='referral_id.currency_id')
    wallet_type = fields.Many2one('wallet.amount.type', string='Wallet Type')
    amount = fields.Monetary(string="Amount")
    date = fields.Date(string="Date")
    remarks = fields.Char(string='Remarks')


class CustomerReferralsSpend(models.Model):
    _name = "customer.referrals.spend"
    _description = "Customer referral Spend"
    
    referral_id = fields.Many2one('customer.referrals', string="Referral")
    currency_id = fields.Many2one('res.currency', string='Currency', related='referral_id.currency_id')
    wallet_type = fields.Many2one('wallet.amount.type', string='Wallet Type')
    amount = fields.Monetary(string="Amount")
    date = fields.Date(string="Date")
    remarks = fields.Char(string='Remarks')



class WalletAmountType(models.Model):
      _name = 'wallet.amount.type'

      name = fields.Char(string="Wallet Type")
      is_refer = fields.Boolean(string="Is Refer")


class ReferralRewardLevels(models.Model):
    _name = 'referral.reward.levels'

    name = fields.Char(string="Name")
    reward_amount = fields.Integer(string="Reward Amount")
    reward_eligible_item_ids = fields.Many2many('product.template', string="Reward Eligible Items")


class OfferWheel(models.Model):
    _name = 'offer.wheel'

    name = fields.Char(string="Name")
    reward_amount = fields.Integer(string="Reward Amount")
    active = fields.Boolean(string="Is Active", default=True)

class WeeklySpinLog(models.Model):
    _name = 'weekly.spin.log'
    _description = 'Weekly Spin Log'

    customer_id = fields.Many2one('res.partner', string='Customer')
    date = fields.Date('Spin Date', default=fields.Date.today())
    wheel_item_id = fields.Many2one('offer.wheel', string='Wheel Item')
