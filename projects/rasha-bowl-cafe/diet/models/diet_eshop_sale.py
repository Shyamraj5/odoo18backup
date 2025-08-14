from odoo import fields,models,api,_
from datetime import datetime
from odoo.exceptions import UserError

class DietEshopSale(models.Model):
    _name = 'diet.eshop.sale'
    _description = 'Diet Eshop Sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", default="New")
    customer_id = fields.Many2one('res.partner', string="Customer")
    available_address_ids = fields.Many2many('res.partner', string="Available Addresses", compute='_compute_available_address_ids')
    address_id = fields.Many2one('res.partner', string="Address", domain=[('id','in',available_address_ids)])
    shift_id = fields.Many2one('customer.shift', string="Shift")
    order_date = fields.Date(string="Order Date", default=fields.Date.today())
    state = fields.Selection([
        ('draft','Draft'),
        ('confirm','Confirm')
    ], default='draft')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    sub_total = fields.Float(string="Sub Total", compute='_compute_total')
    total = fields.Float(string="Total", compute='_compute_total')
    meal_line_ids = fields.One2many('diet.eshop.sale.line', 'order_id', string="Meals")
    delivery_status = fields.Selection([
        ('pending','Pending'),
        ('delivered','Delivered'),
        ('not_delivered','Not Delivered')
    ], default='pending')
    invoice_ids = fields.One2many('account.move', 'eshop_sale_id', string="Invoices")
    invoice_status = fields.Selection([
        ('not_invoiced','Not Invoiced'),
        ('partial','Partially Invoiced'),
        ('full','Fully Invoiced')
    ], default='not_invoiced', compute='_compute_invoice_status')
    payment_status = fields.Selection([
        ('not_paid','Not Paid'),
        ('partial','Partially Paid'),
        ('full','Fully Paid')
    ], default='not_paid', compute='_compute_payment_status')
    invoice_count = fields.Integer(string="Invoice Count", compute='_compute_invoice_count')
    available_points = fields.Float('Available Points', compute='_compute_available_points', store=True)
    applied_points = fields.Float('Applied Points', copy=False)
    spend_id = fields.Many2one('customer.referrals.spend', 'Spend ID')
    driver_order_id = fields.Many2one('driver.order', string="Driver Order")
    promo_code = fields.Char(string="Promo Code")
    promo_discount = fields.Float(string="Promo Discount")
    promo_applied = fields.Boolean(string="Promo Applied")

    @api.depends('customer_id')
    def _compute_available_points(self):
        for order in self:
            points = 0
            if order.customer_id:
                reward_master = self.env["customer.referrals"].search([
                    ('customer_id', '=', order.customer_id.id)
                ], limit=1)
                if reward_master:
                    points = reward_master.balance_amount
            order.available_points = points

    def apply_reward_points(self):
        for order in self:
            if order.available_points >= order.total:
                wallet_type = self.env.ref("diet.eshop_reward_spend_type")
                order.applied_points = order.total
                reward_master = self.env["customer.referrals"].search([
                    ('customer_id', '=', order.customer_id.id)
                ], limit=1)
                spend_id = self.env['customer.referrals.spend'].sudo().create({
                    'referral_id': reward_master.id,
                    'wallet_type': wallet_type.id if wallet_type else False, 
                    'amount': order.applied_points,
                    'date': fields.Date.today(),
                    'remarks': f"Purchased Reward Eligible Item. Referrence No: Eshop {order.name}"
                })
                order.spend_id = spend_id.id
            else:
                raise UserError(_("Not enough points to apply."))
            
    def clear_reward_points(self):
        for order in self:
            if order.applied_points > 0:
                order.applied_points = 0
                order.spend_id.unlink()
                order._compute_available_points()

    @api.depends('invoice_ids')
    def _compute_invoice_status(self):
        for rec in self:
            if rec.invoice_ids:
                if all([invoice.state == 'paid' for invoice in rec.invoice_ids]):
                    rec.invoice_status = 'full'
                else:
                    rec.invoice_status = 'partial'
            else:
                rec.invoice_status = 'not_invoiced'
    @api.depends('invoice_ids')
    def _compute_payment_status(self):
        for rec in self:
            if rec.invoice_ids:
                if all([invoice.payment_state in ['paid', 'in_payment'] for invoice in rec.invoice_ids]):
                    rec.payment_status = 'full'
                elif all([invoice.payment_state == 'not_paid' for invoice in rec.invoice_ids]):
                    rec.payment_status = 'not_paid'
                else:
                    rec.payment_status = 'partial'
            else:
                rec.payment_status = 'not_paid'

    @api.depends('customer_id')
    def _compute_available_address_ids(self):
        for rec in self:
            rec.available_address_ids = rec.customer_id.child_ids.ids

    def action_apply_promo_code(self):
        for rec in self:
            promo_id = self.env['coupon.program'].search([('program_name','=', rec.promo_code),('state', '=', 'active')])
            if not promo_id or promo_id.promocode_used >= promo_id.coupon_count:
                return self.make_response(False, 400, "", None, 'Invalid coupon code.')
            current_day = datetime.today().strftime('%A')
            count = 0
            if promo_id.program_availability == 'custom':
                if promo_id.sunday and current_day == 'Sunday':
                    count += 1
                elif promo_id.monday and current_day == 'Monday':
                    count += 1
                elif promo_id.tuesday and current_day == 'Tuesday':
                    count += 1
                elif promo_id.wednesday and current_day == 'Wednesday':
                    count += 1
                elif promo_id.thursday and current_day == 'Thursday':
                    count += 1
                elif promo_id.friday and current_day == 'Friday':
                    count += 1
                elif promo_id.saturday and current_day == 'Saturday':
                    count += 1
                else:
                    return self.make_response(False, 400, "", None, 'This Promo Code is not available today')
            sub_total = rec.sub_total
            if promo_id.discount_type == 'percentage':
                discount = sub_total * promo_id.program_discount / 100
            else:
                discount = promo_id.program_discount
                
            if sub_total < discount:
                return self.make_response(False, 400, "", None, 'Not Applicable on this subscription')
            rec.promo_discount = discount
            rec.promo_applied = True
    
    def action_remove_promo_code(self):
        for rec in self:
            rec.promo_discount = 0
            rec.promo_applied = False


    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.model_create_multi
    def create(self, val_list):
        for vals in val_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('eshop.order') or 'New'
        return super(DietEshopSale, self).create(val_list)

    @api.depends('meal_line_ids.subtotal', 'promo_discount')
    def _compute_total(self):
        for rec in self:
            rec.write({
                'sub_total': sum(rec.meal_line_ids.mapped('subtotal')),
                'total': sum(rec.meal_line_ids.mapped('subtotal')) - rec.promo_discount
            })

    def action_confirm(self):
        for rec in self:
            # if not rec.address_id:
            #     raise UserError(_("Please select an address to proceed."))
            # if not rec.shift_id:
            #     raise UserError(_("Please select a shift to proceed."))
            driver_order_vals = {
                'eshop_order_id': rec.id,
                'date': rec.order_date,
                'customer_id': rec.customer_id.id,
                'status': 'pending',
                'address_id': rec.address_id.id,
                'shift_id': rec.shift_id.id
            }
            driver_order = self.env['driver.order'].create(driver_order_vals)
            rec.driver_order_id = driver_order
            for line in rec.meal_line_ids:
                line.driver_order_id = driver_order
            rec.state = 'confirm'

    def action_reset(self):
        for rec in self:
            rec.state = 'draft'

    def action_invoice(self):
        for rec in self:
            if (rec.total - rec.applied_points) > 0:
                invoice_lines = []
                for line in rec.meal_line_ids:
                    meal_product_id = self.env['product.product'].search([('product_tmpl_id', '=', line.meal_id.id)], limit=1)
                    invoice_lines.append((0, 0, {
                        'product_id': meal_product_id.id,
                        'quantity': line.quantity,
                        'price_unit': line.price,
                        'name': line.meal_id.name,
                    }))
                if rec.promo_discount > 0:
                    invoice_lines.append((0, 0, {
                        'quantity': 1,
                        'price_unit': -rec.promo_discount,
                        'name': 'Promo Discount',
                    }))
                invoice_vals = {
                    'payment_platform': 'on_line',
                    'partner_id': rec.customer_id.id,
                    'currency_id': rec.currency_id.id,
                    'eshop_sale_id': rec.id,
                    'invoice_line_ids': invoice_lines,
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today()
                }
                invoice = self.env['account.move'].create(invoice_vals)
                invoice.action_post()
                if invoice.amount_total > 0.0:
                    invoice.process_tap_payment()
                rec.invoice_ids += invoice
            else:
                raise UserError(_("Nothing to invoice."))

    def action_view_invoice(self):
        for rec in self:
            action = self.env.ref('account.action_move_out_invoice_type').read()[0]
            action['domain'] = [('id', 'in', rec.invoice_ids.ids)]
            return action
        
    def view_driver_order(self):
        return {
            'name': _('Driver Order'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'driver.order',
            'res_id': self.driver_order_id.id or False,
            'target': 'current',
        }        
    
class DietEshopSaleLine(models.Model):
    _name = 'diet.eshop.sale.line'
    _description = 'Diet Eshop Sale Line'
    
    order_id = fields.Many2one('diet.eshop.sale', string="Order")
    meal_id = fields.Many2one('product.template', string="Meal", domain=[('is_meal', '=', True)])
    quantity = fields.Float(string="Quantity", default=1)
    price = fields.Float(string="Price")
    subtotal = fields.Float(string="Subtotal", compute='_compute_subtotal')
    driver_order_id = fields.Many2one('driver.order', string="Driver Order")

    @api.onchange('meal_id')
    def _onchange_meal_id(self):
        for rec in self:
            rec.price = rec.meal_id.list_price

    @api.depends('quantity', 'price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.price
