from odoo import models, fields, api,_
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class SubscriptionUpgradeWizard(models.TransientModel):
    _name = 'subscription.upgrade.wizard'
    _description = 'Subscription Upgrade Wizard'
    
    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    plan_category_id = fields.Many2one('plan.category', string ="Plan Category")
    plan_id = fields.Many2one('subscription.package.plan', string ="Plan")
    date = fields.Date(string ="Date", default =date.today())
    actual_start_date =fields.Date(string ="Activation Date")
    end_date =fields.Date(string ="End Date")
    balance_amount = fields.Float(string ="Previous subscription Balance", compute ="_compute_prev_subs_balance", store =True)


    @api.onchange('date', 'plan_id')
    def _onchange_subscription_dates(self):
        for rec in self:
            if rec.date and rec.plan_id:
                rec.actual_start_date = rec.date + relativedelta(days=2)
                rec.end_date = rec.actual_start_date + relativedelta(days=(rec.plan_id.duration_days - 1))

    @api.onchange('plan_category_id')
    def _onchange_plan_category_id(self):
        return {
            'domain': {
                'plan_id': [('plan_category_id','in',self.plan_category_id.ids),
                            ('duration_days', '>',self.subscription_id.plan_id.duration_days)]
            }
        }
    
    def button_upgrade(self):
        self.subscription_id.state ='upgraded'
        if self.plan_id:
            meal_line = []
            for meal in self.plan_id.plan_meal_ids:
                meal_line.append((0, 0, {
                    'meal_category_id': meal.meal_category_id.id,
                    "protein": meal.protein,
                    "carbs": meal.carbohydrates,
                    
                }))
        
        upgraded_subscription =self.env['diet.subscription.order'].create({
                    "partner_id" : self.subscription_id.partner_id.id,
                    "plan_category_id" : self.subscription_id.plan_category_id.id,
                    "plan_id" : self.plan_id.id,
                    "start_date" : self.date,
                    "actual_start_date" :self.actual_start_date,
                    "end_date" :self.end_date,
                    "address_id": self.subscription_id.address_id.id,
                    "meal_line_ids" : meal_line,
                    "prev_subs_balance" :self.balance_amount
        })
        upgraded_calendar =self.env['customer.meal.calendar'].search([('so_id','=', self.subscription_id.id),('date','>=',self.actual_start_date)])
        for calendar in upgraded_calendar:
            calendar.state = 'upgraded'
            calendar.reason ="Cancelled due to Upgrade of subscription from " + calendar.so_id.order_number + " to "+ upgraded_subscription.order_number

        upgraded_subscription.message_post_with_view(
                'mail.message_origin_link',
                values={'self': upgraded_subscription, 'origin': self.subscription_id},
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'))
        
        self.subscription_id.message_post_with_view(
                'diet.upgraded_subscription_link',
                values={'self': self.subscription_id, 'origin':upgraded_subscription })
        return {
            "name": _("Subscription Order"),
            "type": "ir.actions.act_window",
            "res_model": "diet.subscription.order",
            "view_mode" : "form",
            "res_id" : upgraded_subscription.id,
            "target": "current",
            
            
        }
    
    @api.depends('subscription_id.plan_id.plan_price',
                 'actual_start_date',
                 'subscription_id.plan_id.duration_days'
                 )
    def _compute_prev_subs_balance(self):
        balance = 0.0
        for rec in self:
            if rec.actual_start_date:
                meal_calendar =self.env['customer.meal.calendar'].search([('so_id','=', self.subscription_id.id),
                                                                          ('date','>=',self.actual_start_date),('is_frozen','=',False)
                                                                          ]).mapped('date')
                date_list =[]
                for dates in meal_calendar:
                    if dates not in date_list:
                        date_list.append(dates)
                left_days = len(date_list)
                if rec.subscription_id.plan_id.duration_days != 0:
                    balance = (rec.subscription_id.plan_id.plan_price * left_days)/rec.subscription_id.plan_id.duration_days
                else:
                    balance = 0.0
                rec.balance_amount = balance

    @api.onchange('subscription_id.actual_start_date','actual_start_date')
    def _onchange_subscription_id(self):
        for rec in self:
            if rec.actual_start_date and (rec.actual_start_date < rec.subscription_id.actual_start_date):
                raise ValidationError(_(f"The Subscription is only start on {rec.subscription_id.actual_start_date.strftime('%d-%m-%Y')}"))
