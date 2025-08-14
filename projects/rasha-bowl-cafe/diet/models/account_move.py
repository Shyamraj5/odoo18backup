from odoo import models, fields, api, _
from lxml import etree
from odoo.exceptions import UserError



class AccountMove(models.Model):
    _inherit = "account.move"

    customer_so_line_id = fields.Many2one('diet.subscription.order', 'Subscription Order', copy=False)
    payment_platform = fields.Selection([
        ('on_line', 'Online'), 
        ('off_line', 'Offline '),('free','Free')],
        string='Payment Platform', default='off_line', tracking=True)
    partner_phone = fields.Char('Partner Phone', related='partner_id.phone')
    discount = fields.Monetary('Discount')
    eshop_sale_id = fields.Many2one('diet.eshop.sale', string="Eshop Sale")

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id, view_type, **options)
        if view_type == "form":
            eview = etree.fromstring(res["arch"])
            payment_paltform_xml_fields = eview.xpath("//field[@name='payment_platform']")
            if payment_paltform_xml_fields:
                user_group = self.env.ref('diet.group_payment_type')
                if user_group in self.env.user.groups_id:
                    payment_paltform_xml_fields[0].set('readonly', 'false')
            res["arch"] = etree.tostring(eview)
        return res

    def print_invoice(self):
        for invoice in self:
            return self.env.ref("account.account_invoices_without_payment").report_action(invoice, config=False)


    def js_assign_outstanding_line(self, line_id):
        self.ensure_one()
        result = super(AccountMove, self).js_assign_outstanding_line(line_id)
        if self.customer_so_line_id.promo_code:
            promo_code = self.customer_so_line_id.promo_code
            promo_id = self.env['coupon.program'].search([('program_name', '=', promo_code)], limit=1)
            existing_participation = promo_id.participation_ids.filtered(lambda p:p.customer_id).mapped('customer_id')
            if not self.customer_so_line_id.partner_id in existing_participation:
                participation_vals = {
                        "customer_id": self.partner_id.id,
                        "applied_code": promo_code,
                        "applied_date": fields.Datetime.now(),
                        "subscription_id": self.customer_so_line_id.id,
                    }
                promo_id.participation_ids = [(0, 0, participation_vals)]
        return result
