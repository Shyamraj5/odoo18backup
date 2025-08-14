# -*- coding: utf-8 -*-


from odoo import fields, models, api
from datetime import date


class SaleOrder(models.Model):
    """ This class is used to inherit sale order"""
    _inherit = 'sale.order'

    subscription_count = fields.Integer(string='Subscriptions',
                                        compute='_compute_subscription_count')
    ref =fields.Char(string='Ref#')
    zone_id = fields.Many2one('customer.zone', string='District')
    mobile = fields.Integer(string='Mobile')
    est_delivery_time = fields.Float(string='Est Delivery Time')
    wallet_amount = fields.Char(string='Wallet Amount')
    super_menus = fields.Char(string='Super Menus')
    date =fields.Date(string='Date')
    order_date =fields.Date(string='Subscription Order Date',readonly=False)
    start_date =fields.Date(string='Start Date',readonly=False)
    end_date = fields.Date(string='End Date')
    plan_id= fields.Many2one('subscription.package.plan', string='plan')
    refund = fields.Float(string='Refund')
    status = fields.Selection([("sale_to_invoice", "Sale To Invoice")],string='Plan Status')
    paid = fields.Float(string='Paid')
    total_amount = fields.Float(string='Subcription Total')
    balance_amount = fields.Float(string='Balance  Amount')
    extra_days = fields.Integer(string='Extra Days')
    remaining_days = fields.Integer(string='Remaining Days')
    generated_days = fields.Integer(string='Generated Days')
    tags = fields.Char(string='Subscription Tags')
    source = fields.Char(string='Subscription Source')
    delivered = fields.Integer(string='Delivered')
    calender = fields.Integer(string='Calender')
    meals = fields.Integer(string='Meals')
    sms = fields.Integer(string='Sms')
    notification = fields.Integer(string='Notification')
    re_subscribe = fields.Integer(string='Re-subscribe')
    is_expired_order = fields.Boolean(string='Is Expired Order',default=False)
    is_not_started = fields.Boolean(string='Is Not started',default=False)
    e_sale_order = fields.Boolean(string='E sale order')
    
    def action_delivered(self):
        return
    
    def action_calender(self):
        return
    
    def action_meals(self):
        return
    
    def action_sms(self):
        return
    
    def action_notification(self):
        return
    
    def action_re_subscribe(self):
        return
    
    def sale_order_expired(self):
        line = self.search([])
        for i in line:  
            if i.end_date :
               if date.today() > i.end_date:
                  i.is_expired_order = True 
               else:              
                   i.is_expired_order = False 
            if i.start_date :
               if date.today() < i.start_date:
                  i.is_not_started = True 
               else:              
                   i.is_not_started = False                

    @api.depends('subscription_count')
    def _compute_subscription_count(self):
        subscription_count = self.env['subscription.package'].search_count(
            [('sale_order', '=', self.id)])
        if subscription_count > 0:
            self.subscription_count = subscription_count
        else:
            self.subscription_count = 0

    def button_subscription(self):
        return {
            'name': 'Subscription',
            'sale_order': False,
            'domain': [('sale_order', '=', self.id)],
            'view_type': 'form',
            'res_model': 'subscription.package',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'context': {
                "create": False
            }
        }



class SubscriptionInherit(models.Model):
    """ This class is used to inherit subscription packages"""
    _inherit = 'subscription.package'

    sale_order_count = fields.Integer()
