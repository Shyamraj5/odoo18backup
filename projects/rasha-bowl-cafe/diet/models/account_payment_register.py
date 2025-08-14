from odoo import models, fields

class AccountPayRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _reconcile_payments(self,to_process, edit_mode=False):
        result = super(AccountPayRegister, self)._reconcile_payments(to_process, edit_mode=False)
        customer_sale_order = self.line_ids[0].move_id.customer_so_line_id
        if customer_sale_order.promo_code:
            promo_code = customer_sale_order.promo_code
            promo_id = self.env['coupon.program'].search([('program_name', '=', promo_code)], limit=1)
            participation_vals = {
                "customer_id": self.partner_id.id,
                "applied_code": promo_code,
                "applied_date": fields.Datetime.now(),
                "subscription_id": customer_sale_order.id,
            }
            promo_id.participation_ids = [(0, 0, participation_vals)]
            
        subscriptions = self.env['diet.subscription.order'].search([
                ('partner_id', '=', customer_sale_order.partner_id.id),
                ('state', '=','paid')
            ])
        referral_id = self.env['customer.referrals'].search([('referral_code','=',customer_sale_order.partner_id.inviter_referral_code)])
        wallet_type = self.env['wallet.amount.type'].search([('is_refer','=',True)])
        if referral_id and len(subscriptions) == 1:
            refer_bonus = self.env['ir.config_parameter'].sudo().get_param('diet.refer_bonus')
            refer_reward = {
                'referral_id': referral_id.id,
                'wallet_type': wallet_type.id, #invite wallet type need to add
                'amount': int(refer_bonus),
                'date': fields.Date.today(),
                'remarks': "Get Rewarded for Invite A Friend"
            }
            referral_id.received_ids = [(0, 0, refer_reward)]
            referral_id._compute_total_balance_amount()

            referer_bonus = self.env['ir.config_parameter'].sudo().get_param('diet.referer_bonus')
            referer_id = self.env['customer.referrals'].search([('customer_id','=',customer_sale_order.partner_id.id)])
            referer_reward = {
                'referral_id': referer_id.id,
                'wallet_type': wallet_type.id, #invite wallet type need to add
                'amount': int(referer_bonus),
                'date': fields.Date.today(),
                'remarks': "Get Rewarded for Join Via Friend"
            }
            referer_id.received_ids = [(0, 0, referer_reward)]
            referer_id._compute_total_balance_amount()
        return result