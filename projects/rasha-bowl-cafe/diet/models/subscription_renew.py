# -*- coding: utf-8 -*-


import datetime
from odoo import api, models, fields


class SaleOrder(models.Model):
    """Inherited sale order model"""
    _inherit = "sale.order"

    is_subscription = fields.Boolean(string='Is Subscription', default=False)
    subscription_id = fields.Many2one('diet.subscription.order',
                                      string='Subscription')
    sub_reference = fields.Char(string="Sub Reference Code", store=True)
