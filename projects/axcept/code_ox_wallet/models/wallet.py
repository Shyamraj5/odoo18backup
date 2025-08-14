from odoo import models, fields, api

class WalletWallet(models.Model):
    _name = "wallet.wallet"
    _description = "Customer Wallet"

    customer_id = fields.Many2one('res.partner', string="Customer Name")
    total_received = fields.Monetary(string="Total Received", compute='_compute_totals', store=True)
    total_paid = fields.Monetary(string="Total Paid", compute='_compute_totals', store=True)
    balance_amount = fields.Monetary(string="Balance Amount", compute='_compute_total_balance_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='customer_id.currency_id')
    received_ids = fields.One2many('wallet.received', 'wallet_id', string="Received")
    spend_ids = fields.One2many('wallet.spend', 'wallet_id', string="Spent")

    @api.depends('received_ids.amount', 'spend_ids.amount')
    def _compute_totals(self):
        for record in self:
            total_received = sum(record.received_ids.mapped('amount'))
            total_paid = sum(record.spend_ids.mapped('amount'))
            record.total_received = total_received
            record.total_paid = total_paid

    @api.depends('total_received', 'total_paid')
    def _compute_total_balance_amount(self):
        for record in self:
            record.balance_amount = record.total_received - record.total_paid


class WalletReceived(models.Model):
    _name = "wallet.received"
    _description = "Wallet Received"

    wallet_id = fields.Many2one('wallet.wallet', string="Wallet")
    currency_id = fields.Many2one('res.currency', string='Currency', related='wallet_id.currency_id')
    amount = fields.Monetary(string="Amount")


class WalletSpend(models.Model):
    _name = "wallet.spend"
    _description = "Wallet Spend"

    wallet_id = fields.Many2one('wallet.wallet', string="Wallet")
    currency_id = fields.Many2one('res.currency', string='Currency', related='wallet_id.currency_id')
    amount = fields.Monetary(string="Amount")
