# -*- coding: utf-8 -*-


from odoo import api, models, fields


class AccountMove(models.Model):
    """Inherited sale order model"""
    _inherit = "account.move"

    is_subscription = fields.Boolean(string='Is Subscription', default=False)
    subscription_id = fields.Many2one('subscription.package',
                                      string='Subscription')

class Product(models.Model):
    """Inherited product template model"""
    _inherit = "product.template"

    is_subscription = fields.Boolean(string='Is Subscription', default=False)
    subscription_plan_id = fields.Many2one('subscription.package.plan',
                                           string='Subscription Plan')
    plan_category_id = fields.Many2many('plan.category', string="Plan Category", tracking=True)
