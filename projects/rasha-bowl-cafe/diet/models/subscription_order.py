from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo import exceptions
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import random
import string
from lxml import etree
import requests
from pytz import timezone


class DietSubscriptionOrder(models.Model):
    _name = "diet.subscription.order"
    _description = "Subscription Order"
    _rec_name = "order_number"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    customer_id = fields.Char(related='partner_id.customer_sequence_no', string="Customer ID", tracking=True)
    order_number = fields.Char(string ="Order No", copy =False)
    date = fields.Date(string ="Date", default=fields.Date.today(), tracking =True)
    partner_id = fields.Many2one('res.partner', string ="Customer", tracking =True)
    plan_category_id = fields.Many2one('plan.category', string='Plan Category', tracking =True)
    plan_id = fields.Many2one('subscription.package.plan', string ="Plan", tracking =True, required=True)
    available_plan_choice_ids = fields.Many2many('plan.choice', compute='_compute_available_plan_choice_ids', store=True)
    plan_choice_id = fields.Many2one('plan.choice',string="Plan Choice", required=True)
    start_date = fields.Date(string ="Start Date", default=fields.Date.today(), tracking =True)
    end_date = fields.Date(string ="End Date", tracking =True)
    state = fields.Selection([('draft', 'Draft'),
                                    ('paid', 'Confirm'),
                                    ('in_progress', 'In Progress'),
                                    ('upgraded','Upgraded'),
                                    ('hold', 'Freeze'),
                                    ('closed', 'Expired'),
                                    ('pending','Pending'),
                                    ('active','Active')], default='draft', string ="Plan Status", tracking =True)
    payment_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid')
    ], string='Payment Status', compute='_compute_payment_status', store=True, tracking =True)
    sales_person_id = fields.Many2one('res.users', string ="Created By", tracking =True, default=lambda self: self.env.user)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    plan_base_price = fields.Monetary('Price', currency_field="currency_id", compute='get_plan_price', store=True, tracking =True)
    addons_price = fields.Monetary('Meals Additional Price', currency_field="currency_id", compute='_compute_amount', store=True, tracking =True)
    manual_price = fields.Monetary('Manual Additional Price',currency_field='currency_id', tracking =True)
    total = fields.Float(string ="Total", compute='_compute_amount', store=True)
    per_day_price = fields.Float(string ="Per Day Price", compute='_compute_amount', store=True)
    paid_amount = fields.Float(string ="Paid Amount")
    balance_amount = fields.Float(string ="Balance Amount")
    promo_code = fields.Char(string ="Promo-code")
    order_id = fields.Many2one('res.partner', string ="Order Id")
    choice_ids = fields.Many2many('subscription.plan.choice', string='Choices', compute='_compute_choice_ids')
    choice_id = fields.Many2one('subscription.plan.choice', string='Choice', domain="[('id', 'in', choice_ids)]")
    meal_line_ids = fields.One2many('subscription.meal.line', 'cus_sale_order_line_id', string ="Meal Line", tracking =True)
    is_closed = fields.Boolean(string="Closed", default=False)
    close_reason = fields.Many2one('subscription.package.stop',
                                   string='Close Reason')
    closed_by = fields.Many2one('res.users', string='Closed By')
    close_date = fields.Date(string='Closed on')
    to_renew = fields.Boolean(string='To Renew', default=False)
    actual_start_date = fields.Date(string="Actual Start Date",tracking =True)
    previous_start_date = fields.Date(string="Previous Start Date",tracking =True)
    is_subscription_moved = fields.Boolean(string="Is Subscription Moved", default=False)
    invoice_ids = fields.One2many('account.move', 'customer_so_line_id', string='Invoices')
    invoiced_amount = fields.Monetary('Invoiced Amount', compute='_compute_invoiced_amount', store=True)
    amount_due = fields.Monetary('Amount Due', compute='_compute_invoiced_amount', store=True, tracking =True)
    sale_order_ids = fields.One2many('sale.order', 'sale_order_subscription', string='Sale Orders')
    address_ids = fields.Many2many('res.partner', string='Available Addresses', compute='_compute_address_ids')
    address_id = fields.Many2one('res.partner', string='Address')
    invoice_count = fields.Integer('Invoice Count', compute='_compute_invoice_count')
    coupon_code = fields.Char('Coupon Code')
    coupon_discount = fields.Float('Discount', default=0)
    is_coupon_code_applied = fields.Boolean('Is COupon COde Applied')
    tax_ids = fields.Many2many('account.tax', string='Taxes', default=lambda self: self.env.company.account_sale_tax_id)
    amount_tax = fields.Monetary('VAT', compute='_compute_amount', store=True)
    untaxed_total = fields.Monetary('Untaxed Total', compute='_compute_amount', store=True)
    grand_total = fields.Float('Net price', compute='_compute_amount', store=True)
    prev_subs_balance = fields.Float(string ="Previous Subscription Balance")
    sub_end_in = fields.Integer(string="Subscription Ends In",compute='_compute_subscription_end_in')
    active = fields.Boolean(string='Archived', default=True)
    sunday = fields.Boolean(string='Sunday', default=False)
    monday = fields.Boolean(string='Monday', default=False)
    tuesday = fields.Boolean(string='Tuesday', default=False)
    wednesday = fields.Boolean(string='Wednesday', default=False)
    thursday = fields.Boolean(string='Thursday', default=False)
    friday = fields.Boolean(string='Friday', default=False)
    saturday = fields.Boolean(string='Saturday', default=False)
    carbs = fields.Float(string ="Carbs", tracking =True, default=0)
    protein = fields.Float(string ="Protein", tracking =True, default=0)
    pc_combination = fields.Char('PC Combination', compute='_compute_pc_combination', store=True)
    payment_type =fields.Selection([('on_line','Online'),('off_line','Offline'),('free','Free')],
                                   string ="Payment Type", default='off_line', tracking=True)
    pay_later = fields.Boolean(string='Pay Later', default=False)
    meal_count_ids = fields.One2many(comodel_name='meals.count', inverse_name='meal_subscription_id', string='Meal Count', domain=[('is_ramdan', '=', False)])
    additional_meal_count_ids = fields.One2many(comodel_name='meals.count', inverse_name='meal_subscription_id', string='Meal Count', domain=[('is_ramdan', '=', False),('additional_meal', '=', True)])
    ramdan_meal_count_ids = fields.One2many(comodel_name='meals.count', inverse_name='ramdan_subscription_id', string='Meal Count (Ramdan)', domain=[('is_ramdan', '=', True)])
    referral_code = fields.Char(string ="Referral Code")
    package_days = fields.Integer(string="Package Days", compute="_compute_package_days")
    additional_days = fields.Integer(string="Additional Days")
    paid_by = fields.Many2one('res.users', string='Paid By')
    promo_code_discount = fields.Float('Promo Code Discount')
    calories = fields.Float(string = "Calories")
    phone = fields.Char(related='partner_id.phone',string='Phone')
    created_by = fields.Many2one('res.partner',string="Created by user")
    fat = fields.Float(string ="Fat", default=0.0)
    meal_calendar_ids = fields.One2many('customer.meal.calendar', 'so_id', string='Meal Calendar')
    freezed_meal_calendar_ids = fields.One2many('customer.meal.calendar', 'so_id', string='Meal Calendar', domain=[('state', '=', 'freezed')])
    meal_not_set = fields.Boolean(string='Meal not set',compute="_compute_is_not_set")
    existing_subscription_available_days = fields.Integer(string="Existing Subscription Available Days",compute="_compute_days_left")
    total_days = fields.Integer(string="Total Days", compute='_compute_total_days', store=True)
    meal_selection_ids = fields.One2many('customer.meal.calendar', 'so_id', string='Meal Selection', domain=[('state', 'in', ['active', 'active_with_meal', 'freezed'])])
    available_points = fields.Float('Available Points', compute='_compute_available_points', store=True)
    applied_points = fields.Float('Applied Points', default=0, copy=False)
    spend_id = fields.Many2one('customer.referrals.spend', 'Spend ID')
    ramdan_plan_applied = fields.Boolean('Ramdan Plan Applied')
    ramdan_plan_id = fields.Many2one('subscription.package.plan', string="Plan", tracking=True)
    available_ramdan_plan_choice_ids = fields.Many2many('plan.choice', 'ramdan_subs_id', 'ramdan_choice_id', compute='_compute_available_ramdan_plan_choice_ids', store=True)
    ramdan_plan_choice_id = fields.Many2one('plan.choice',string="Plan Choice")
    is_ramdan_plan = fields.Boolean('Is Ramdan Plan', compute='_compute_is_ramdan_plan')
    is_freezed = fields.Boolean('Is Freezed', compute='_compute_is_freezed', store=True)
    no_of_people = fields.Integer('Number of People')
    veg_or_non_veg = fields.Selection([('vegetarian', 'Vegetarian'), ('non_vegetarian', 'Non-Vegetarian')], string='Vegetarian or Non-Vegetarian')
    tiffin_box = fields.Boolean(default=False, string='Tiffin Box Needed')
    boiled_egg = fields.Boolean(default=False, string='Include Boiled Eggs')
    no_of_veg = fields.Integer('Number of Vegetarian')
    customer_address_id = fields.Many2one('res.partner', string='Address')
    choice_config_id = fields.Many2one('choice.config', string='Choice Configuration', domain="[('meal_category_config_id', '=', plan_id)]")
    addtional_meals_config_ids = fields.One2many('subscription.additional.meals',inverse_name='subscription_id',string='Additional Meals Config',)



    @api.depends('meal_calendar_ids.state')
    def _compute_is_freezed(self):
        for subscription in self:
            is_freezed = False
            if subscription.state == 'in_progress':
                self.env.cr.execute("""
                    select sub.id
                    from diet_subscription_order as sub
                    join customer_meal_calendar as cal on cal.so_id=sub.id
                    join auditlog_log as audit on audit.res_id=cal.id
                    join auditlog_http_request as http on audit.http_request_id=http.id
                    where sub.state='in_progress'
                    and cal.state='freezed'
                    and audit.name='freezed'
                    and http.name in ('/freeze_subscription','/web/dataset/call_button')
                    group by sub.id
                """)
                result = self.env.cr.fetchall()
                if result:
                    result = [r[0] for r in result]
                else:
                    result = []
                if subscription.id in result:
                    is_freezed = True
            subscription.is_freezed = is_freezed

    @api.depends('plan_id', 'ramdan_plan_id')
    def _compute_is_ramdan_plan(self):
        for record in self:
            record.is_ramdan_plan = record.plan_id.is_ramdan_plan or record.ramdan_plan_id.is_ramdan_plan

    @api.depends('customer_id')
    def _compute_available_points(self):
        for order in self:
            points = 0
            if order.partner_id:
                reward_master = self.env["customer.referrals"].search([
                    ('customer_id', '=', order.partner_id.id)
                ], limit=1)
                if reward_master:
                    points = reward_master.balance_amount
            order.available_points = points

    def apply_reward_points(self):
        for order in self:
            if order.available_points >= order.total:
                wallet_type = self.env.ref("diet.subscription_reward_spend_type")
                order.applied_points = order.total
                reward_master = self.env["customer.referrals"].search([
                    ('customer_id', '=', order.partner_id.id)
                ], limit=1)
                spend_id = self.env['customer.referrals.spend'].sudo().create({
                    'referral_id': reward_master.id,
                    'wallet_type': wallet_type.id if wallet_type else False, 
                    'amount': order.applied_points,
                    'date': fields.Date.today(),
                    'remarks': f"Purchased Subscription with Reward Points. Subscription No: {order.order_number}"
                })
                order.spend_id = spend_id.id
                order._compute_available_points()
            else:
                raise UserError(_("Not enough points to apply."))
            
    def clear_reward_points(self):
        for order in self:
            if order.applied_points > 0:
                order.applied_points = 0
                order.spend_id.unlink()
                order._compute_available_points()
    
    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id, view_type, **options)
        if view_type == "form":
            eview = etree.fromstring(res["arch"])
            xml_fields = eview.xpath("//field[@name='actual_start_date']")
            if xml_fields:
                # Get the user's timezone or use the company's timezone
                user_tz = self.env.context.get('tz') or self.env.company.partner_id.tz or 'UTC'
                user_timezone = timezone(user_tz)                
                current_datetime = datetime.now(user_timezone)
                company = self.env.company
                today_date = current_datetime.date()
                # Get the subscription buffer days from system parameters
                buffer_days = int(self.env['ir.config_parameter'].sudo().get_param('diet.subscription_create_buffer', default=0))
                date = today_date + relativedelta(days=buffer_days)
                date_str = date.strftime("%Y-%m-%d")
                options_str = (
                    xml_fields[0].get("options", "{}")
                    .replace("{", "{'min_date': '%s'" % date_str))
                xml_fields[0].set("options", options_str)
            payment_type_xml_fields = eview.xpath("//field[@name='payment_type']")
            if payment_type_xml_fields:
                user_group = self.env.ref("diet.group_payment_type")
                if user_group in self.env.user.groups_id:
                    payment_type_xml_fields[0].set("readonly", "false")

            res["arch"] = etree.tostring(eview)
        return res

    def unlink(self):
        for record in self:
            if not self.env.user.has_group('diet.group_subscription_delete') and record.invoice_ids:
                raise UserError(_("You don't have access to delete this record."))
            invoices = record.invoice_ids
            for inv in invoices:
                payment_transactions = inv.transaction_ids
                if payment_transactions:
                    payment_transactions.sudo().with_context(skip_group_check=True).unlink()
                payments = inv._get_reconciled_payments()
                if payments:
                    payments.action_draft()
                    payments.unlink()
                
                inv.button_draft()
                inv.unlink()
            meal_calendar = self.env['customer.meal.calendar'].search([('so_id','=',record.id)])
            if meal_calendar:
                meal_calendar.unlink()
            sale_orders = record.sale_order_ids
            if sale_orders:
                sale_orders.with_context(disable_cancel_warning=True).action_cancel()
                sale_orders.unlink()

        return super(DietSubscriptionOrder, self).unlink()
    
    @api.depends('invoice_ids.amount_residual', 'amount_due', 'invoice_ids.payment_state','state')
    def _compute_payment_status(self):
        for subscription in self:
            if subscription.state == 'closed':
                if subscription.payment_type == 'free':
                    subscription.payment_status = 'paid'
                else:
                    amount_due = subscription.amount_due
                    amount_total = sum(subscription.invoice_ids.mapped('amount_total'))
                    invoice_amount_due = sum(subscription.invoice_ids.mapped('amount_residual'))
                    
                    if amount_due == 0:
                        if invoice_amount_due == 0:
                            subscription.payment_status = 'paid'
                        elif invoice_amount_due > 0 and invoice_amount_due < amount_total:
                            subscription.payment_status = 'partial'
                        else:
                            subscription.payment_status = 'not_paid'
                    elif amount_due > 0 and invoice_amount_due < amount_total:
                        subscription.payment_status = 'partial'
                    else:
                        subscription.payment_status = 'not_paid'
            elif subscription.state == 'draft':
                subscription.payment_status = 'not_paid'
            else:
                amount_due = subscription.amount_due
                amount_total = sum(subscription.invoice_ids.mapped('amount_total'))
                invoice_amount_due = sum(subscription.invoice_ids.mapped('amount_residual'))
                if subscription.payment_type == 'free':
                    subscription.payment_status = 'paid'
                    subscription.state = 'in_progress'
                elif amount_due == 0:
                    if invoice_amount_due == 0:
                        subscription.payment_status = 'paid'
                    elif invoice_amount_due > 0 and invoice_amount_due < amount_total:
                        subscription.payment_status = 'partial'
                    else:
                        subscription.payment_status = 'not_paid'
                elif amount_due > 0 and invoice_amount_due < amount_total:
                    subscription.payment_status = 'partial'
                elif amount_due == amount_total:
                    subscription.payment_status = 'not_paid'
                else:
                    subscription.payment_status = 'not_paid'

    def add_additional_meals(self):
        self.ensure_one()

        plan_choice = self.plan_choice_id
        additional_meals = plan_choice.addtional_meal_ids

        line_vals = []
        for meal in additional_meals.filtered(lambda m: m.meal_id and m.meal_category_id):
            line_vals.append((0, 0, {
                'meal_id': meal.meal_id.id,
                'price': meal.price or 0.0,
                'count': meal.default_count or 1,
                'meal_category_id': meal.meal_category_id.id,
            }))

        wizard = self.env['additional.meal.wizard'].create({
            'subscription_order_id': self.id,
            'line_ids': line_vals,
        })
       

        return {
            'name': _('Additional Meal'),
            'type': 'ir.actions.act_window',
            'res_model': 'additional.meal.wizard',
            'context': {
                'default_subscription_order_id': self.id
            },
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }


    def apply_default_meals(self):
        for subscription in self:
            start_date = fields.Date.today()
            ramdan_start_date = self.env.company.ramdan_start_date
            ramdan_end_date = self.env.company.ramdan_end_date
            while start_date <= subscription.end_date:
                if (
                    ramdan_start_date
                    and ramdan_end_date
                    and ramdan_start_date <= start_date <= ramdan_end_date
                ):
                    ramdan = True
                else:
                    ramdan = False
                calendar_entries = subscription.meal_calendar_ids.filtered(lambda cal: 
                    cal.date == start_date
                    and cal.meal_selection_by != 'customer'
                    and cal.state not in ['freezed','off_day','closed']
                    and cal.delivery_status == 'not_delivered'
                    and cal.is_additional_meal == False
                ).sorted(key=lambda cal: cal.meal_category_id.name)
                count = 0
                category_id = False
                for calendar in calendar_entries:
                    # Determine the appropriate plan based on Ramadan status
                    if ramdan:
                        # First try the dedicated Ramadan plan if it exists and is a Ramadan plan
                        if subscription.ramdan_plan_id and subscription.ramdan_plan_id.is_ramdan_plan:
                            plan = subscription.ramdan_plan_id
                        # If regular plan is marked as Ramadan plan, use it
                        elif subscription.plan_id.is_ramdan_plan:
                            plan = subscription.plan_id
                        # Fallback to regular plan
                        else:
                            plan = subscription.plan_id
                    else:
                        # Outside Ramadan, use regular plan
                        # if part of ramdan plan
                        if subscription.plan_id.is_ramdan_plan:
                            plan = subscription.ramdan_plan_id
                        else:
                            plan = subscription.plan_id
                    default_meal_rec = self.env['plan.default.meals'].search([
                        ('meal_category_id', '=', calendar.meal_category_id.id),
                        ('plan_id', '=', plan.id),
                    ])
                    default_meals = False
                    if default_meal_rec:
                        if calendar.weekday == '0':
                            default_meals = default_meal_rec.monday_meal_ids
                        elif calendar.weekday == '1':
                            default_meals = default_meal_rec.tuesday_meal_ids
                        elif calendar.weekday == '2':
                            default_meals = default_meal_rec.wednesday_meal_ids
                        elif calendar.weekday == '3':
                            default_meals = default_meal_rec.thursday_meal_ids
                        elif calendar.weekday == '4':
                            default_meals = default_meal_rec.friday_meal_ids
                        elif calendar.weekday == '5':
                            default_meals = default_meal_rec.saturday_meal_ids
                        elif calendar.weekday == '6':
                            default_meals = default_meal_rec.sunday_meal_ids
                    if category_id != calendar.meal_category_id.id:
                        category_id = calendar.meal_category_id.id
                    else:
                        count += 1
                    if default_meals:
                        if count > len(default_meals) - 1:
                            count = 0
                            category = False
                        calendar.meal_id = default_meals[count].id
                        calendar.meal_selection_by = 'system'
                        calendar._onchange_state()
                start_date += timedelta(days=1)

    @api.onchange('plan_id', 'actual_start_date', 'end_date')
    def _check_plan_validation(self):
        for rec in self:
            if rec.plan_id and rec.plan_id.start_date and rec.plan_id.end_date and rec.actual_start_date and rec.end_date:
                start = rec.plan_id.start_date
                end = rec.plan_id.end_date
                if rec.is_ramdan_plan and not (start <= rec.actual_start_date <= end):
                    raise UserError(_("Please Ensure the plan is valid in the Date"))
                elif not (rec.actual_start_date >= start and rec.end_date <= end):
                    raise UserError(_("Please Ensure the plan is valid in the Date"))
                
            if rec.plan_id and not rec.plan_id.is_ramdan_plan:
                if not rec.plan_id.inverse_plan_id:
                    rec.ramdan_plan_id = False
                    rec.ramdan_plan_choice_id = False
                    rec.ramdan_meal_count_ids = [(5, 0, 0)]



    @api.depends(
        'actual_start_date', 'end_date', 'additional_days',
        'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'
    )
    def _compute_total_days(self):
        for record in self:
            start = record.actual_start_date
            end = record.end_date
            days_count = 0
            excluded_weekdays = []
            if not record.monday:
                excluded_weekdays.append(0)
            if not record.tuesday:
                excluded_weekdays.append(1)
            if not record.wednesday:
                excluded_weekdays.append(2)
            if not record.thursday:
                excluded_weekdays.append(3)
            if not record.friday:
                excluded_weekdays.append(4)
            if not record.saturday:
                excluded_weekdays.append(5)
            if not record.sunday:
                excluded_weekdays.append(6)
            if record.meal_calendar_ids:
                meal_calendar_ids = record.meal_calendar_ids.filtered(lambda cal: cal.state in ['active', 'active_with_meal'])
                dates = meal_calendar_ids.mapped('date') if meal_calendar_ids else False
                if dates:
                    dates = list(set(dates))
                days_count = len(dates) if dates else 0
            else:
                if start and end:
                    while start <= end:
                        if start.weekday() not in excluded_weekdays:
                            days_count += 1
                        start += timedelta(days=1)
                    if record.additional_days:
                        days_count += record.additional_days
                    if end.weekday() in excluded_weekdays:
                        days_count += 1
            record.total_days = days_count

    @api.depends('invoice_ids.amount_total', 'grand_total')
    def _compute_invoiced_amount(self):
        for record in self:
            record.invoiced_amount = sum(record.invoice_ids.filtered(lambda inv: inv.state not in ['cancel']).mapped('amount_total'))
            record.amount_due = record.grand_total - record.invoiced_amount

    def create_invoice(self):
        for record in self:
            if record.partner_id and record.partner_id.customer_address_id:
                plan_product_id = self.env['product.template'].search([
                    ('plan_id', '=', record.plan_id.id)
                ], limit=1)
                if not plan_product_id:
                    raise UserError(_("Related product not found for this plan."))
                plan_product_variant_id = self.env['product.product'].search([
                    ('product_tmpl_id', '=', plan_product_id.id)
                ], limit=1)
                price_unit = record.total - sum(record.invoice_ids.filtered(lambda inv: inv.state not in ['cancel']).mapped('amount_untaxed'))
                invoice = self.env['account.move'].create({
                    'partner_id': record.partner_id.id,
                    'customer_so_line_id': record.id,
                    'invoice_origin': f"{record.order_number}",
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'product_id': plan_product_variant_id.id,
                        'name': plan_product_variant_id.name,
                        'price_unit': price_unit,
                        'quantity': 1
                    })],
                    'move_type': 'out_invoice'
                })
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': invoice.id,
                    'view_mode': 'form',
                    'target': 'current',
                }

    @api.depends('end_date')
    def _compute_days_left(self):
        for record in self:
            existing_subscription_available_days = 0
            existing_subscription = self.env['diet.subscription.order'].search([
                ('partner_id', '=', record.partner_id.id),
                ('state', '=', 'in_progress'),
                ('end_date', '>', date.today()),
                ('id', '!=', record._origin.id)
            ], limit=1)
            if existing_subscription:
                current_date = date.today()
                available_days = (existing_subscription.end_date - current_date).days
                existing_subscription_available_days = available_days
            record.existing_subscription_available_days = existing_subscription_available_days

    @api.depends('protein', 'carbs')
    def _compute_pc_combination(self):
        for record in self:
            record.pc_combination = f"P{int(record.protein)}/C{int(record.carbs)}"

    @api.depends('meal_calendar_ids.meal_id')
    def _compute_is_not_set(self):
        if not any(self.meal_calendar_ids.mapped('meal_id')):
            self.meal_not_set = True
        else:
            self.meal_not_set = False

    def verify_promo_code(self):
        for rec in self:
            if not rec.promo_code:
                raise UserError(_("Please enter a promo code."))
            promo_code_upper = rec.promo_code.upper()
            promo_id = self.env['coupon.program'].search([('program_name', '=', promo_code_upper), ('state','=', 'active')], limit=1)
            if not promo_id:
                raise UserError(_("Invalid Promo Code."))
            if not promo_id.no_partner_limit:
                promo_usage = self.env['program.participated.customers'].search([('program_id', '=', promo_id.id), ('customer_id', '=', rec.partner_id.id)], limit=1)
                if promo_usage:
                    raise UserError(_("This promo code has already been applied by the customer."))

            if not promo_id.is_universal_code:
                selected_choice = rec.plan_choice_id
                applicable_choices = promo_id.plan_applicable_ids.mapped('appl_choice_ids')
                if applicable_choices and selected_choice not in applicable_choices:
                    raise ValidationError(_('The selected plan and choice are not applicable for this promo code.'))

            if promo_id.program_availability == 'custom':
                day_mapping = {
                    'Sunday': promo_id.sunday,
                    'Monday': promo_id.monday,
                    'Tuesday': promo_id.tuesday,
                    'Wednesday': promo_id.wednesday,
                    'Thursday': promo_id.thursday,
                    'Friday': promo_id.friday,
                    'Saturday': promo_id.saturday,
                }
                current_day = datetime.today().strftime('%A')
                if not day_mapping.get(current_day):
                    raise UserError(_("This Promo Code is not available today"))

            if promo_id.program_type == 'promocode':
                if promo_id.promocode_used < promo_id.coupon_count:
                    if not promo_id.is_universal_code:
                        applicable_plan_line = promo_id.plan_applicable_ids.filtered(lambda app_line: selected_choice in app_line.appl_choice_ids)
                        if applicable_plan_line.discount_type == 'percentage':
                            discount_percentage = applicable_plan_line.program_discount
                            discount_amount = rec.total * discount_percentage / 100
                        else:
                            discount_amount = applicable_plan_line.program_discount
                    else:
                        if promo_id.discount_type == 'percentage':
                            discount_amount = rec.total * promo_id.program_discount / 100
                        else:
                            discount_amount = promo_id.program_discount
                    if rec.total < discount_amount:
                        raise UserError(_("Not Applicable on this subscription"))
                    rec.promo_code_discount = discount_amount
                else:
                    raise UserError(_("Code expired."))
            else:
                coupon_id = self.env['coupon.program.code'].search([('coupon_code', '=', rec.promo_code)], limit=1)
                if not coupon_id:
                    raise UserError(_("Invalid Coupon."))
                if coupon_id.state == 'used':
                    raise UserError(_("Coupon already used."))
                if coupon_id.coupon_program_id.state == 'expired':
                    raise UserError(_("Coupon expired."))

                rec.promo_code_discount = rec.total * coupon_id.coupon_program_id.program_discount / 100
                coupon_id.state = 'used'
            rec.is_coupon_code_applied = True

    
    def clear_promo_code(self):
        for rec in self:
            rec.promo_code = False
            rec.promo_code_discount = 0
            rec.is_coupon_code_applied = False
            promo_id = self.env['coupon.program'].search([('program_name','=',rec.promo_code)])
            if promo_id.program_type == 'promocode':
                promo_id.promocode_used -= 1
                participation = promo_id.participation_ids.filtered(lambda part: part.customer_id == rec.partner_id.id and part.subscription_id == rec.id)
                if participation:
                    participation[-1].unlink()
            else:
                coupon_id = self.env['coupon.program.code'].search([('coupon_code','=',rec.promo_code)], limit=1)
                coupon_id.state = 'unused'

    @api.depends('plan_choice_id.no_of_day')
    def _compute_package_days(self):
        for plan in self:
            plan.package_days = plan.plan_choice_id.no_of_day if plan.plan_choice_id else 0

    @api.depends('plan_id')
    def _compute_available_plan_choice_ids(self):
        for subs in self:
            subs.available_plan_choice_ids = False
            if subs.plan_id and subs.plan_id.day_choice_ids:
                subs.available_plan_choice_ids = [
                    (4,choice.id) for choice in subs.plan_id.day_choice_ids
                ]

    @api.depends('ramdan_plan_id')
    def _compute_available_ramdan_plan_choice_ids(self):
        for subs in self:
            subs.available_ramdan_plan_choice_ids = False
            if subs.ramdan_plan_id and subs.ramdan_plan_id.day_choice_ids:
                subs.available_ramdan_plan_choice_ids = [
                    (4,choice.id) for choice in subs.ramdan_plan_id.day_choice_ids
                ]


    @api.onchange('plan_choice_id')
    def available_days(self):
        for rec in self:
            if rec.plan_choice_id:
                rec.sunday = rec.plan_choice_id.sunday
                rec.monday = rec.plan_choice_id.monday
                rec.tuesday = rec.plan_choice_id.tuesday
                rec.wednesday = rec.plan_choice_id.wednesday
                rec.thursday = rec.plan_choice_id.thursday
                rec.friday = rec.plan_choice_id.friday
                rec.saturday = rec.plan_choice_id.saturday
            else:
                rec.sunday = False
                rec.monday = False
                rec.tuesday = False
                rec.wednesday = False
                rec.thursday = False
                rec.friday = False
                rec.saturday = False
            # rec.plan_base_price = rec.plan_choice_id.plan_price

    @api.depends('choice_config_id', 'total_days', 'plan_choice_id')
    def get_plan_price(self):
        for rec in self:
            if rec.plan_choice_id.meal_config_ids:
                rec.plan_base_price = rec.plan_choice_id.meal_config_ids[0].additional_price * rec.total_days
            else:
                rec.plan_base_price = 0.                    
    @api.onchange('plan_choice_id')               
    def onchange_meal_count_generation(self):
        for subs in self:
            if not subs.plan_id or not subs.plan_id.meal_config_ids:
                return
            ramdan_meals = subs.meal_count_ids.filtered(lambda meal_count: meal_count.is_ramdan)
            subs.meal_count_ids = [(5, 0, 0)]
            if ramdan_meals:
                subs.meal_count_ids = [(4, meal.id, 0) for meal in ramdan_meals]
            if subs.plan_id and subs.plan_id.meal_config_ids:
                meal_lines = [
                    (0, 0, {
                        'meal_category_id': meal.meal_category_id.id,
                        'base_meal_count': meal.meal_count,
                        'additional_price': meal.additional_price,
                        'additional_count': meal.meal_count,
                        'is_ramdan': False
                    })
                    for meal in subs.plan_id.meal_config_ids
                ]
                subs.meal_count_ids = meal_lines


    @api.onchange('actual_start_date','ramdan_plan_id')               
    def _onchange_ramdan_meal_count_generation(self):
        for subs in self:
            subs.ramdan_meal_count_ids = [(5, 0, 0)]
            if not subs.plan_id:
                return
            plan = None
            if subs.plan_id.is_ramdan_plan and subs.plan_id.inverse_plan_id:
                plan = subs.plan_id.inverse_plan_id
            elif not subs.plan_id.is_ramdan_plan and subs.plan_id.ramdan_plan_id:
                plan = subs.plan_id.ramdan_plan_id
            if plan and plan.meal_config_ids:
                meal_lines = []
                for meal in plan.meal_config_ids:
                    meal_lines.append(
                        (0, 0, {
                            'meal_category_id': meal.meal_category_id.id,
                            'base_meal_count': meal.meal_count,
                            'additional_price': meal.additional_price,
                            'additional_count': meal.meal_count,
                            'is_ramdan': True 
                        })
                    )
                subs.ramdan_meal_count_ids = meal_lines

    def _get_end_date(self, excluded_weekdays, choice_days, start_date):
        count = 1
        end_date = start_date
        while count < choice_days:
            if end_date.weekday() not in excluded_weekdays:
                count += 1
            end_date += timedelta(days=1)
        while end_date.weekday() in excluded_weekdays:
            end_date += timedelta(days=1)
        return end_date
    
    def minus_days(self):
        if self.additional_days:
            return {
                'name': _('Minus days'),
                'type': 'ir.actions.act_window',
                'res_model': 'extent.minus.days.wizard',
                'view_mode': 'form',
                'context': {
                    'default_subscription_id': self.id
                },
                'target': 'new'
            }
        

    @api.onchange(
        'plan_choice_id','actual_start_date', 'sunday', 'monday',
        'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'
    )
    def _onchange_end_date(self):
        for record in self:
            if record.actual_start_date and record.plan_choice_id:
                start_date = fields.Datetime.from_string(record.actual_start_date)
                week = 7
                excluded_weekdays = []
                if not record.monday:
                    excluded_weekdays.append(0)
                if not record.tuesday:
                    excluded_weekdays.append(1)
                if not record.wednesday:
                    excluded_weekdays.append(2)
                if not record.thursday:
                    excluded_weekdays.append(3)
                if not record.friday:
                    excluded_weekdays.append(4)
                if not record.saturday:
                    excluded_weekdays.append(5)
                if not record.sunday:
                    excluded_weekdays.append(6)
                end_date = self._get_end_date(excluded_weekdays, record.plan_choice_id.no_of_day, start_date)
                record.end_date = end_date.date()
            else:
                record.end_date = False

            ramdan_start_date = self.env.company.ramdan_start_date
            ramdan_end_date = self.env.company.ramdan_end_date
            if (
                record.actual_start_date
                and ramdan_start_date
                and ramdan_end_date
                and ramdan_start_date <= record.actual_start_date <= ramdan_end_date
            ) or (
                record.end_date
                and ramdan_start_date
                and ramdan_end_date
                and ramdan_start_date <= record.end_date <= ramdan_end_date
            ):
                if not record.plan_id.is_ramdan_plan:
                    ramdan_plan = record.plan_id.ramdan_plan_id
                    if not ramdan_plan:
                        raise UserError(_("This subscription overlaps with ramdan season but related ramdan plan not configured in the subscription plan."))
                    ramdan_plan_choice = ramdan_plan.day_choice_ids.filtered(lambda choice: choice.no_of_day == record.plan_choice_id.no_of_day)
                    record.ramdan_plan_id = ramdan_plan.id
                    record.ramdan_plan_choice_id = ramdan_plan_choice.id
                else:
                    inverse_plan = record.plan_id.inverse_plan_id
                    if not inverse_plan:
                        raise UserError(_("This subscription overlaps with ramdan season but related alternate plan not configured in the subscription plan."))
                    inverse_plan_choice = inverse_plan.day_choice_ids.filtered(lambda choice: choice.no_of_day == record.plan_choice_id.no_of_day)
                    record.ramdan_plan_id = inverse_plan.id
                    record.ramdan_plan_choice_id = inverse_plan_choice.id

    @api.onchange('actual_start_date')
    def _onchange_actual_start_date(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        user_has_bypass_access = self.env.user.has_group('diet.group_bypass_order_limit')
        todays_subscriptions = self.env['diet.subscription.order'].search([('actual_start_date', '=', self.actual_start_date)])
        todays_subscriptions_count = len(todays_subscriptions)
    
    def _compute_subscription_end_in(self):
        for rec in self:
            state = rec.env['customer.meal.calendar'].search([('so_id','=',rec.id),('state','in',['active','active_with_meal'])])
            active_dates = list(set(state.mapped('date')))
            active_days =len([dates for dates in active_dates if dates > fields.Date.today()])
            remaining_days = (active_days)
            rec.sub_end_in = remaining_days
            
    @api.constrains('start_date', 'end_date', 'partner_id', 'plan_id')
    def _check_subscription_overlap(self):
        for subscription in self:
            overlapping_subscriptions_query = """SELECT id FROM diet_subscription_order WHERE partner_id = %s AND id != %s AND state IN ('in_progress') 
                                                AND ('%s' BETWEEN actual_start_date AND end_date
                                                OR '%s' BETWEEN actual_start_date AND end_date) 
                                                AND plan_id = %s """ % (
                subscription.partner_id.id, subscription.id, subscription.actual_start_date.strftime('%Y-%m-%d'), 
                subscription.end_date.strftime('%Y-%m-%d'), subscription.plan_id.id
            )
            self.env.cr.execute(overlapping_subscriptions_query)
            overlapping_subscriptions = self.env.cr.fetchall()
            if overlapping_subscriptions and not self.env.context.get('skip_subscription_overlap_check'):
                raise exceptions.ValidationError(
                    "The subscription period for customer overlaps with another subscription." 
                )

    def check_subscription_overlap(self, start_date, end_date, partner_id):
        for subscription in self:
            overlapping_subscriptions_query = """SELECT id FROM diet_subscription_order WHERE partner_id = %s AND id != %s AND state IN ('in_progress') 
                                                AND ('%s' BETWEEN actual_start_date AND end_date
                                                OR '%s' BETWEEN actual_start_date AND end_date)""" % (
                subscription.partner_id.id, subscription.id, subscription.actual_start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
            )
            self.env.cr.execute(overlapping_subscriptions_query)
            overlapping_subscriptions = self.env.cr.fetchall()
            if overlapping_subscriptions and not self.env.context.get('skip_subscription_overlap_check'):
                raise exceptions.ValidationError(
                    "The subscription period for customer overlaps with another subscription." 
                )

    def apply_coupon(self):
        for rec in self:
            if rec.coupon_code:
                coupon_id = self.env['coupon.program.code'].search([('coupon_code','=',rec.coupon_code)], limit=1)
                if not coupon_id:
                    raise UserError(_("Invalid Coupon."))
                if coupon_id.state == 'used':
                    raise UserError(_("Coupon already used."))
                if coupon_id.coupon_program_id.state == 'expired':
                    raise UserError(_("Coupon expired."))
                rec.coupon_discount = rec.total * coupon_id.coupon_program_id.program_discount/100
                coupon_id.state = 'used'
                rec.is_coupon_code_applied = True

    def apply_customer_selected_meals(self, meal_calendar_list):
        for meal_calendar in meal_calendar_list:
            date = meal_calendar.get('date')
            meal_category_id = meal_calendar.get('meal_category_id')
            current_meal_calendar_ids = self.meal_calendar_ids.filtered(lambda cal: cal.date == date and cal.meal_category_id.id == meal_category_id 
                                                                        and cal.state in ['active', 'active_with_meal'] and cal.meal_selection_by != 'customer')
            if current_meal_calendar_ids:
                current_meal_calendar_ids[0].write({
                    'meal_id': meal_calendar.get('meal_id'),
                    'meal_selection_by': meal_calendar.get('meal_selection_by')
                })

    def apply_freezed_meals(self, meal_calendar_list):
        for meal_calendar in meal_calendar_list:
            date = meal_calendar.get('date')
            meal_category_id = meal_calendar.get('meal_category_id')
            current_meal_calendar_ids = self.meal_calendar_ids.filtered(lambda cal: cal.date == date and cal.state != 'freezed')
            for current_meal_calendar in current_meal_calendar_ids:
                current_meal_calendar.write({
                    'state': 'freezed'
                })


    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for subscription in self:
            subscription.invoice_count = len(subscription.invoice_ids)

    @api.depends('partner_id')
    def _compute_address_ids(self):
        for subs in self:
            if subs.partner_id:
                address_ids = self.env['res.partner'].search([
                    ('parent_id','=',subs.partner_id.id)
                ])
                subs.address_ids = False
                subs.address_ids = [(4, addr.id) for addr in address_ids]
            else:
                subs.address_ids = False

    @api.model_create_multi
    def create(self,vals):
        for val in vals:
            if not val.get('order_number') or val['order_number'] == _('New'):
                val['order_number'] = self.env['ir.sequence'].next_by_code('order.code') or _('New')
                val['created_by'] = self.env.user.partner_id.id
        return super().create(vals)

    @api.onchange('plan_category_id')
    def _onchange_plan_category_id(self):
        return {
            'domain': {
                'plan_id': [('plan_category_id','in',self.plan_category_id.ids)]
            }
        }

    def open_subscription_order(self):
        return {
            "name": _("Subscription Order"),
            "res_model": "diet.subscription.order",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current"
        }

    def view_meal_calendar(self):
        return {
            "name": _("Meal Calendar"),
            "res_model": "customer.meal.calendar",
            "type": "ir.actions.act_window",
            "view_mode": "calendar,kanban,list,form",
            "target": "current",
            "domain": [
                ('partner_id','=',self.partner_id.id),
                ('date','>=',self.actual_start_date),
                ('so_id', '=', self.id),
                ('date','<=',self.end_date)
            ]
        }

    def action_in_progress(self):
        for rec in self:
            rec.state = 'in_progress'

    def action_hold(self):
        return {
            'name': _('Subscription Freeze'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.freeze.wizard',
            'context': {
                'default_subscription_id': self.id
            },
            'view_mode': 'form',
            'target': 'new'
        }

    def action_freeze_all(self):
        return {
            'name': _('Subscription Freeze All'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.freeze.wizard',
            'context': {
                'default_subscription_ids': self.ids
            },
            'view_mode': 'form',
            'target': 'new'
        }


    
    def action_upgrade(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise ValidationError(_("The Subscription is not started"))
        return {
            'name': _('Subscription Upgrade'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.upgrade.wizard',
            'context': {
                'default_subscription_id': self.id,
                'default_plan_category_id': self.plan_category_id.id,
                'default_mode': 'freeze'
            },
            'view_mode': 'form',
            'target': 'new'
        }

    def action_unhold(self):
        return {
            'name': _('Subscription Un-Freeze'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.freeze.wizard',
            'context': {
                'default_subscription_id': self.id,
                'default_mode': 'unfreeze'
            },
            'view_mode': 'form',
            'target': 'new'
        }


    def action_close(self):
        """ Button for subscription close wizard """
        return {
            'name': "Subscription Close Reason",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'subscription.close.wizard',
            'target': 'new',
            'context': {
                'default_subscription_id': self.id}
        }
        
    def activate_subscription_cron(self):
        day_after_tomorrow = date.today() + timedelta(days=2)
        subscriptions_to_activate = self.env['diet.subscription.order'].sudo().search([
            ('state', '=', 'paid'),
            ('payment_status', '=', 'paid'),
            ('actual_start_date', '=', day_after_tomorrow)
        ])
        for subscription in subscriptions_to_activate:
            try:
                subscription.activate_subscription()
                subscription.generate_meal_calendar()
            except:
                raise UserError(_(f"Subscription activation failed for {subscription.order_number}"))

    def update_closed_state(self):
        match = self.env['diet.subscription.order'].search([
            ('state', 'in', ['in_progress']),
            '|',
            ('end_date', '<', fields.Date.today()),
            ('close_date', '=', fields.Date.today())
        ])
        for i in match:
            i.write({'state': 'closed'})

    @api.depends('plan_id')
    def _compute_choice_ids(self):
        for rec in self:
            choice_list_ids = []
            choice_ids = self.env['subscription.plan.choice'].search([('plan_id', '=', rec.plan_id.id)]).sorted(key=lambda r: r.name)
            choice_name = False
            for choice in choice_ids:
                if choice.name != choice_name:
                    choice_list_ids.append(choice.id)
                    choice_name = choice.name
            choices_ids = self.env['subscription.plan.choice'].search([('id', 'in', choice_list_ids)])
            rec.choice_ids = choices_ids


    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        for rec in self:
            if rec.plan_id:
                if rec.plan_id and rec.plan_id != rec.plan_choice_id.plan_config_day_id:
                    rec.plan_choice_id = False
                rec.protein = rec.plan_id.protein
                rec.carbs = rec.plan_id.carbohydrates
                rec.calories = rec.plan_id.calories
            else:
                rec.protein = 0.0
                rec.carbs = 0.0 
                rec.calories = 0.0
            rec.available_days()

    @api.depends(
        'choice_id',
        'meal_line_ids.default_count',
        'meal_line_ids.count',
        'meal_line_ids.meal_category_id',
        'meal_count_ids.sub_total',
        'coupon_discount',
        'promo_code_discount',
        'plan_choice_id',
        'manual_price',
        'actual_start_date',
        'end_date',
        'tax_ids',
        'applied_points',
        'payment_type'
    )
    def _compute_amount(self):
        for rec in self:
            if rec.payment_type == 'free':
                rec.update({
                    "addons_price": 0.0,
                    "per_day_price": 0.0,
                    "total": 0.0,
                    "grand_total": 0.0
                })
                continue
            plan_price = rec.plan_base_price
            addons_price = 0
            if self.env.context.get('add_additional_charge'):
                addons_price = rec.addons_price
            manual_price = rec.manual_price
            addtional_meal_price = sum(
                    line.price * line.count * rec.total_days
                    for line in rec.addtional_meals_config_ids
                ) if rec.addtional_meals_config_ids else 0.0

            if not self.env.context.get('skip_base_price_calculation'):
                for price in rec.meal_count_ids:
                    addons_price += price.sub_total
                addons_price += addtional_meal_price
                base_price = plan_price + addons_price + manual_price
                base_per_day_price = base_price / rec.plan_choice_id.no_of_day if rec.plan_choice_id and rec.plan_choice_id.no_of_day else 0
                total_days = (rec.end_date - rec.actual_start_date).days if rec.end_date and rec.actual_start_date else 0
                total_price = base_per_day_price * rec.total_days
            else:
                total_price = plan_price + addons_price + manual_price
                base_per_day_price = total_price / rec.plan_choice_id.no_of_day if rec.plan_choice_id and rec.plan_choice_id.no_of_day else 0
            untaxed_amount = round((total_price - rec.coupon_discount - rec.promo_code_discount), 2) - rec.applied_points
            amount_tax_obj = rec.tax_ids.compute_all(untaxed_amount)
            amount_tax = sum([tax['amount'] for tax in amount_tax_obj['taxes']])
            rec.update({
                "addons_price": round(addons_price, 2),
                "per_day_price": round(base_per_day_price, 2),
                "total": round(total_price, 2),
                "untaxed_total": untaxed_amount,
                "amount_tax": amount_tax,
                "grand_total": amount_tax_obj['total_included'],
            })


    def write(self, vals):
        res = super(DietSubscriptionOrder, self).write(vals)
        if any(key in vals for key in ['manual_price', 'plan_choice_id', 'meal_count_ids', 'coupon_discount', 'promo_code_discount']):
            for record in self:
                record._compute_amount()
                record.write({
                    'plan_base_price': record.plan_base_price,
                    'addons_price': record.addons_price,
                    'total': record.total,
                    'grand_total': record.grand_total,
                })
        return res


    def generate_meal_calendar(self):
        for order in self:
            if not order.meal_calendar_ids:
                start_date = order.actual_start_date
                end_date = order.end_date
                order._check_subscription_overlap()
                ramdan_start_date = self.env.company.ramdan_start_date
                ramdan_end_date = self.env.company.ramdan_end_date
                while start_date <= end_date:
                    if (
                        ramdan_start_date
                        and ramdan_end_date
                        and ramdan_start_date <= start_date <= ramdan_end_date
                    ):
                        is_ramdan = True
                    else:
                        is_ramdan = False
                    day_of_date = str(start_date.weekday())
                    day_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                        shift.period=='day_of_week'
                    )
                    schedule_line = False
                    shift = False
                    address = False
                    if not schedule_line:
                        schedule_line = day_shifts.filtered(lambda shift:
                            shift.day_of_week == day_of_date
                        )
                        shift = schedule_line.shift_type if schedule_line else False
                        address = schedule_line.address_id if schedule_line else False
                    if not schedule_line:
                        range_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                            shift.period=='date_range'
                        )
                        schedule_line = range_shifts.filtered(lambda shift:
                            shift.from_date <= start_date <= shift.to_date
                        )
                        shift = schedule_line.shift_type if schedule_line else False
                        address = schedule_line.address_id if schedule_line else False
                    if not schedule_line:
                        shift = order.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                        address = order.partner_id.customer_address_id
                    if is_ramdan:
                        if order.plan_id.is_ramdan_plan:
                            available_meal = order.meal_count_ids
                            plan = order.plan_id
                        else:
                            available_meal = order.ramdan_meal_count_ids
                            plan = order.ramdan_plan_id
                    else:
                        if order.plan_id.is_ramdan_plan:
                            available_meal = order.ramdan_meal_count_ids
                            plan = order.ramdan_plan_id
                        else:
                            available_meal = order.meal_count_ids
                            plan = order.plan_id
                    meal_category_ids=[]
                    for record in available_meal:
                        if record.additional_count > 0:
                            category_ids=record.meal_category_id.ids
                            meal_category_ids.append(category_ids[0])
                    off_day = False
                    if day_of_date == '0':
                        off_day = not order.monday
                    elif day_of_date == '1':
                        off_day = not order.tuesday
                    elif day_of_date == '2':
                        off_day = not order.wednesday
                    elif day_of_date == '3':
                        off_day = not order.thursday
                    elif day_of_date == '4':
                        off_day = not order.friday
                    elif day_of_date == '5':
                        off_day = not order.saturday
                    elif day_of_date == '6':
                        off_day = not order.sunday
                    if off_day:
                        self.env['customer.meal.calendar'].create({
                            "date": start_date,
                            "partner_id": order.partner_id.id,
                            "so_id": order.id,
                            "state" :'off_day',
                            "off_day" :off_day,
                        })
                    else:
                        for i in meal_category_ids:
                            meal_count = available_meal.filtered(lambda meal: meal.meal_category_id.id == i)
                            for j in range(int(meal_count.additional_count)):
                                meal_calendar = self.env['customer.meal.calendar'].create({
                                    "date": start_date,
                                    "partner_id": order.partner_id.id,
                                    "so_id": order.id,
                                    "meal_category_id":i,
                                    "plan_category_id": order.plan_category_id.id,
                                    "shift_id" : shift.id if shift else False,
                                    "address_id" : address.id if address else False
                                })
                                meal_calendar._onchange_state()
                        for config in order.addtional_meals_config_ids:
                            for i in range(config.count):
                                self.env['customer.meal.calendar'].create({
                                    "date": start_date,
                                    "partner_id": order.partner_id.id,
                                    "so_id": order.id,
                                    "meal_category_id": config.meal_category_id.id,
                                    "plan_category_id": order.plan_category_id.id,
                                    "shift_id": shift.id if shift else False,
                                    "address_id": address.id if address else False,
                                    "meal_id": config.meal_id.id,
                                    "is_paid_day": True,
                                    "is_additional_meal": True,
                                })._onchange_state()
                    start_date += timedelta(days=1)
                order.apply_default_meals()
            else:
                raise ValidationError(_("Meal calendar already generated."))

    def generate_meal_calendar_ramdan(self, start_date=False, end_date=False):
        for order in self:
            og_start_date = start_date
            og_end_date = end_date
            while start_date <= end_date:
                day_of_date = str(start_date.weekday())
                day_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                    shift.period=='day_of_week'
                )
                schedule_line = False
                shift = False
                address = False
                if not schedule_line:
                    schedule_line = day_shifts.filtered(lambda shift:
                        shift.day_of_week == day_of_date
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    range_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                        shift.period=='date_range'
                    )
                    schedule_line = range_shifts.filtered(lambda shift:
                        shift.from_date <= start_date <= shift.to_date
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    shift = order.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                    address = order.partner_id.customer_address_id
                available_meal = order.ramdan_meal_count_ids
                meal_category_ids=[]
                for record in available_meal:
                    if record.additional_count > 0:
                        category_ids=record.meal_category_id.ids
                        meal_category_ids.append(category_ids[0])
                off_day = False
                if day_of_date == '0':
                    off_day = not order.monday
                elif day_of_date == '1':
                    off_day = not order.tuesday
                elif day_of_date == '2':
                    off_day = not order.wednesday
                elif day_of_date == '3':
                    off_day = not order.thursday
                elif day_of_date == '4':
                    off_day = not order.friday
                elif day_of_date == '5':
                    off_day = not order.saturday
                elif day_of_date == '6':
                    off_day = not order.sunday
                if off_day:
                    self.env['customer.meal.calendar'].create({
                        "date": start_date,
                        "partner_id": order.partner_id.id,
                        "so_id": order.id,
                        "state" :'off_day',
                        "off_day" :off_day,
                    })
                else:
                    for i in meal_category_ids:
                        meal_count = order.ramdan_meal_count_ids.filtered(lambda meal: meal.meal_category_id.id == i)
                        for j in range(int(meal_count.additional_count)):
                            meal_calendar = self.env['customer.meal.calendar'].create({
                                "date": start_date,
                                "partner_id": order.partner_id.id,
                                "so_id": order.id,
                                "meal_category_id":i,
                                "plan_category_id": order.ramdan_plan_id.plan_category_id.id if order.ramdan_plan_id.plan_category_id else False,
                                "shift_id" : shift.id if shift else False,
                                "address_id" : address.id if address else False,
                            })
                            meal_calendar._onchange_state()
                start_date += timedelta(days=1)
            order.apply_default_meals_by_date_range(og_start_date, og_end_date, ramdan=True)

    def apply_default_meals_by_date_range(self, start_date, end_date, ramdan=False):
        for subscription in self:
            while start_date <= end_date:
                calendar_entries = subscription.meal_calendar_ids.filtered(lambda cal: 
                    cal.date == start_date
                    and cal.meal_selection_by != 'customer'
                    and cal.state not in ['freezed','off_day','closed']
                ).sorted(key=lambda cal: cal.meal_category_id.name)
                count = 0
                category_id = False
                if ramdan:
                    plan = subscription.ramdan_plan_id
                else:
                    plan = subscription.plan_id
                for calendar in calendar_entries:
                    default_meal_rec = self.env['plan.default.meals'].search([
                        ('meal_category_id', '=', calendar.meal_category_id.id),
                        ('plan_id', '=', plan.id),
                    ])
                    default_meals = False
                    if default_meal_rec:
                        if calendar.weekday == '0':
                            default_meals = default_meal_rec.monday_meal_ids
                        elif calendar.weekday == '1':
                            default_meals = default_meal_rec.tuesday_meal_ids
                        elif calendar.weekday == '2':
                            default_meals = default_meal_rec.wednesday_meal_ids
                        elif calendar.weekday == '3':
                            default_meals = default_meal_rec.thursday_meal_ids
                        elif calendar.weekday == '4':
                            default_meals = default_meal_rec.friday_meal_ids
                        elif calendar.weekday == '5':
                            default_meals = default_meal_rec.saturday_meal_ids
                        elif calendar.weekday == '6':
                            default_meals = default_meal_rec.sunday_meal_ids
                    if category_id != calendar.meal_category_id.id:
                        category_id = calendar.meal_category_id.id
                    else:
                        count += 1
                    if default_meals:
                        if count > len(default_meals) - 1:
                            count = 0
                            category = False
                        calendar.meal_id = default_meals[count].id
                        calendar._onchange_state()
                start_date += timedelta(days=1)

    def generate_meal_calendar_by_date_range(self, start_date, end_date):
        for order in self:
            ramdan_start_date = self.env.company.ramdan_start_date
            ramdan_end_date = self.env.company.ramdan_end_date
            while start_date <= end_date:
                if (
                    ramdan_start_date
                    and ramdan_end_date
                    and ramdan_start_date <= start_date <= ramdan_end_date
                ):
                    is_ramdan = True
                else:
                    is_ramdan = False
                day_of_date = str(start_date.weekday())
                day_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                    shift.period=='day_of_week'
                )
                schedule_line = False
                shift = False
                address = False
                if not schedule_line:
                    schedule_line = day_shifts.filtered(lambda shift:
                        shift.day_of_week == 'day_of_date'
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    range_shifts = order.partner_id.shift_ids.filtered(lambda shift:
                        shift.period=='date_range'
                    )
                    schedule_line = range_shifts.filtered(lambda shift:
                        shift.from_date <= start_date <= shift.to_date
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    shift = order.partner_id.customer_address_id.shift_id if order.partner_id.customer_address_id else False
                    address = order.partner_id.customer_address_id
                if is_ramdan:
                    if order.plan_id.is_ramdan_plan:
                        available_meal = order.meal_count_ids
                        plan = order.plan_id
                    else:
                        available_meal = order.ramdan_meal_count_ids
                        plan = order.ramdan_plan_id
                else:
                    if order.plan_id.is_ramdan_plan:
                        available_meal = order.ramdan_meal_count_ids
                        plan = order.ramdan_plan_id
                    else:
                        available_meal = order.meal_count_ids
                        plan = order.plan_id
                meal_category_ids=[]
                for record in available_meal:
                    if record.additional_count > 0:
                        category_ids=record.meal_category_id.ids
                        meal_category_ids.append(category_ids[0])
                off_day = False
                if day_of_date == '0':
                    off_day = not order.monday
                elif day_of_date == '1':
                    off_day = not order.tuesday
                elif day_of_date == '2':
                    off_day = not order.wednesday
                elif day_of_date == '3':
                    off_day = not order.thursday
                elif day_of_date == '4':
                    off_day = not order.friday
                elif day_of_date == '5':
                    off_day = not order.saturday
                elif day_of_date == '6':
                    off_day = not order.sunday
                if off_day:
                    self.env['customer.meal.calendar'].create({
                        "date": start_date,
                        "partner_id": order.partner_id.id,
                        "so_id": order.id,
                        "state" :'off_day',
                        "off_day" :off_day,
                    })
                else:
                    for i in meal_category_ids:
                        meal_count = sum(available_meal.filtered(lambda meal: meal.meal_category_id.id == i).mapped('additional_count'))
                        for j in range(int(meal_count)):
                            meal_calendar = self.env['customer.meal.calendar'].create({
                                "date": start_date,
                                "partner_id": order.partner_id.id,
                                "so_id": order.id,
                                "meal_category_id":i,
                                "plan_category_id": order.plan_category_id.id,
                                "shift_id" : shift.id if shift else False,
                                "address_id" : address.id if address else False,
                                "is_paid_day": True
                            })
                            meal_calendar._onchange_state()
                            self._compute_total_days()
                            self.meal_calendar_ids |= meal_calendar
                start_date += timedelta(days=1)
            order.apply_default_meals()
            
    def activate_subscription(self):
        for subscription in self:
            if subscription.state in ["paid"]:
                subscription.state = "in_progress"
            else:
                raise ValidationError(_("Subscription not paid."))

    def confirm(self):
        for subscription in self:
            # check if there is any subscription between the start and end date
            existing_subscription_query = """SELECT id FROM diet_subscription_order WHERE partner_id = %s AND id != %s AND state IN ('in_progress') 
                                            AND ('%s' BETWEEN actual_start_date AND end_date
                                            OR '%s' BETWEEN actual_start_date AND end_date)
                                            AND plan_id = %s
                                            """   % (
                subscription.partner_id.id, subscription.id, subscription.actual_start_date.strftime('%Y-%m-%d'), 
                subscription.end_date.strftime('%Y-%m-%d'), subscription.plan_id.id
            )
            self.env.cr.execute(existing_subscription_query)
            existing_subscription = self.env.cr.fetchone()
            if existing_subscription:
                raise ValidationError(_(f"There is already a subscription between {subscription.actual_start_date.strftime('%d-%m-%Y')} and {subscription.end_date.strftime('%d-%m-%Y')}."))
                
            """Method to create a sale order and invoice based on the subscription"""
            
            if subscription.payment_type != 'free':
                if subscription.grand_total != 0:
                    invoice = subscription.prepare_invoice()
                    invoice.payment_platform = subscription.payment_type
                    invoice.action_post()
                    # if subscription.payment_type == 'on_line' and not subscription.pay_later and not self.env.context.get('from_mobile'):
                    #     self.create_invoice_tap_link(invoice)
                else:
                    promo_id = self.env['coupon.program'].search([('program_name', '=', self.promo_code)], limit=1)
                    existing_participation = promo_id.participation_ids.filtered(lambda p: p.customer_id).mapped('customer_id')
                    if not subscription.partner_id in existing_participation:
                        participation_vals = {
                            "customer_id": subscription.partner_id.id,
                            "applied_code": promo_id.program_name,
                            "applied_date": fields.Datetime.now(),
                            "subscription_id": subscription.id,
                        }
                        promo_id.participation_ids = [(0, 0, participation_vals)]
                subscription.state = 'paid'
            else:
                invoice = subscription.prepare_invoice()
                invoice.customer_so_line_id = subscription.id
                invoice.payment_platform = subscription.payment_type
                invoice.action_post()

                # Create a participation record for the FREE promo code
                if self.grand_total == 0.0:
                    promo_id = self.env['coupon.program'].search([('program_name', '=', self.promo_code)], limit=1)
                    participation_vals = {
                        "customer_id": subscription.partner_id.id,
                        "applied_code": promo_id.program_name,
                        "applied_date": fields.Datetime.now(),
                        "subscription_id": subscription.id,
                    }
                    promo_id.participation_ids = [(0, 0, participation_vals)]
            subscription.state = 'paid'

    def prepare_invoice(self):
        self.ensure_one()
        payment_platform = 'off_line'
        if self.payment_type == 'on_line' and not self.pay_later and not self.env.context.get('from_mobile'):
            payment_platform = 'on_line'

        # Create the invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'customer_so_line_id': self.id,
            'invoice_origin': self.order_number,
            'invoice_date': fields.Date.today(),
            'payment_platform': payment_platform
        })

        # Add invoice line for the subscription plan
        product = self.env['product.product'].search([
            ('plan_id', '=', self.plan_id.id), 
            ('is_plan', '=', True)
        ], limit=1)

        if not product:
            raise UserError(_("Related product not found for this plan."))

        invoice_line = {
            'product_id': product.id,
            'name': self.plan_id.name,
            'quantity': 1,
            'price_unit': self.untaxed_total if self.payment_type != 'free' else 0,
            'tax_ids': [(6, 0, self.tax_ids.ids)]
        }
        invoice.write({'invoice_line_ids': [(0, 0, invoice_line)]})
        
        return invoice

    def view_sub_sale_order(self):
        if self.sale_order_ids:
            sale_order_id = self.sale_order_ids.id

            return {
                'name': 'Sale Order',
                'view_type': 'form',
                'res_model': 'sale.order',
                'res_id': sale_order_id,
                'view_mode': 'form',
                'type': 'ir.actions.act_window',
            }

        else:
            return {
                'type': 'ir.actions.act_window_close',
            }


    def view_invoice(self):
        if len(self.invoice_ids) > 1:
            return {
                "name": _("Subscription Invoice"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "domain": [('id','in',self.invoice_ids.ids)],
                "view_mode": "list,form",
                "target": "current"
            }
        else:
            return {
                "name": _("Subscription Invoice"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": self.invoice_ids[0].id,
                "view_mode": "form",
                "target": "current"
            }

    def extend_subscription(self):
        for record in self:
            if record.package_days == 1 and not self.env.user.has_group('diet.group_subscription_extension'):
                plan_name = record.plan_choice_id.name if record.plan_choice_id else "unknown plan"
                raise ValidationError(_(
                    "You cannot extend a subscription for the '%s' plan."
                ) % plan_name)  
        return {
            'name': _('Extend Subscription'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.extension.wizard',
            'view_mode': 'form',
            'context': {
                'default_subscription_id': self.id
            },
            'target': 'new'
        }
    
    def reschedule_entries(self):
        start_date = date(2025, 3, 30)
        meal_calendar_entries = self.env['customer.meal.calendar'].search([('date', '>', '2025-03-30'), ("meal_category_id.is_ramdan", "=", True)])
        subscriptions = meal_calendar_entries.mapped('so_id')
        for subscription in subscriptions:
            freezed_meal_calendar_list = []
            for meal_calendar in subscription.meal_calendar_ids.filtered(lambda x: x.date >= start_date and x.state == 'freezed'):
                vals = {
                    'date': meal_calendar.date,
                    'meal_category_id': meal_calendar.meal_category_id.id,
                    'meal_id': meal_calendar.meal_id.id,
                    'meal_selection_by': meal_calendar.meal_selection_by,
                    'state': meal_calendar.state
                }
                freezed_meal_calendar_list.append(vals)
            subscription.meal_calendar_ids.filtered(lambda x: x.date >= start_date).unlink()
            subscription.generate_meal_calendar_by_date_range(start_date, subscription.end_date)
            subscription.apply_default_meals_by_date_range(start_date, subscription.end_date)
            subscription.apply_freezed_meals(freezed_meal_calendar_list)

    @api.onchange('protein', 'carbs')
    def _onchange_calories(self):
        calories = 0.0
        if self.protein:
            calories += self.protein * 4
        if self.carbs:
            calories += self.carbs * 4
        self.calories = calories

    def check_off_day(self, calendar_date):
        off_days = []
        if not self.sunday:
            off_days.append(6)
        if not self.monday:
            off_days.append(0)
        if not self.tuesday:
            off_days.append(1)
        if not self.wednesday:
            off_days.append(2)
        if not self.thursday:
            off_days.append(3)
        if not self.friday:
            off_days.append(4)
        if not self.saturday:
            off_days.append(5)
        while calendar_date.weekday() in off_days:
            return True
        return False

    def get_new_start_date(self, start_date):
        off_days = []
        if not self.sunday:
            off_days.append(6)
        if not self.monday:
            off_days.append(0)
        if not self.tuesday:
            off_days.append(1)
        if not self.wednesday:
            off_days.append(2)
        if not self.thursday:
            off_days.append(3)
        if not self.friday:
            off_days.append(4)
        if not self.saturday:
            off_days.append(5)
        while start_date.weekday() in off_days:
            start_date += timedelta(days=1)
        return start_date


    def freeze_subscription_day(self, freeze_date,is_bulk_freeze=False):
        if not self:
            raise ValidationError(_("Subscription not passed."))
        if not freeze_date:
            raise ValidationError(_("Freeze date not passed."))   
        off_days = []
        if not self.sunday:
            off_days.append(6)
        if not self.monday:
            off_days.append(0)
        if not self.tuesday:
            off_days.append(1)
        if not self.wednesday:
            off_days.append(2)
        if not self.thursday:
            off_days.append(3)
        if not self.friday:
            off_days.append(4)
        if not self.saturday:
            off_days.append(5)
        if freeze_date.weekday() in off_days:
            return
        calendar_ids = self.env['customer.meal.calendar'].search([
            ('date', '=', freeze_date),
            ('so_id', '=', self.id),
             ('state', '!=', 'freezed')
        ])
        if not calendar_ids:
            if self.env.context.get('universal_pause'):
                freezed_calendar_ids = self.env['customer.meal.calendar'].search([
                    ('date', '=', freeze_date),
                    ('so_id', '=', self.id),
                    ('state', '=', 'freezed')
                ])
                for calendar in freezed_calendar_ids:
                    calendar.state = 'off_day'
                self.message_post(
                    body=f"Subscription frozen for {freeze_date} by Universal Pause Days [{self.env.context.get('pause_reason', '')}]",
                )
                return
            else:
                raise ValidationError(_(f"Nothing to freeze on {freeze_date.strftime('%b %d, %Y')}"))
        calendar_ids.sorted(lambda c: c.meal_category_id)
        new_end_date = self.end_date + timedelta(days=1)
        while new_end_date.weekday() in off_days:
            off_day_calendar_entry = self.env['customer.meal.calendar'].sudo().create({
                'date': new_end_date,
                'so_id': self.id,
                'state': 'off_day',
                "partner_id": self.partner_id.id,
            })
            off_day_calendar_entry._compute_display_name()
            new_end_date += timedelta(days=1)
        self.generate_meal_calendar_by_date_range(new_end_date, new_end_date)
        for calendar in calendar_ids:
            if self.env.context.get('universal_pause'):
                calendar.state = 'off_day'
            else:
                calendar.state = 'freezed'
            calendar._compute_display_name()
        if self.env.context.get('universal_pause'):
            self.message_post(
                body=f"Subscription frozen for {freeze_date} by Universal Pause Days [{self.env.context.get('pause_reason', '')}]",
            )
        self.with_context(skip_subscription_overlap_check=True).write({
            'end_date': new_end_date
        })
        self.apply_default_meals()
        self.with_context(skip_base_price_calculation=True)._compute_amount()

        # move forward any overlapping subscriptions
        upcoming_subscriptions = self.env['diet.subscription.order'].search([
            ('partner_id', '=', self.partner_id.id),
            ('id', '!=', self.id),
            ('state', 'in', ['paid','in_progress']),
            ('actual_start_date', '>=', freeze_date)
        ])
        this_new_end_date = self.end_date
        donot_consider_subs = self.env['diet.subscription.order']
        for upcoming_subscription in upcoming_subscriptions:
            if upcoming_subscription in donot_consider_subs:
                continue
            overlapping_subscription = self.env['diet.subscription.order']
            remaining_subscriptions = upcoming_subscriptions.filtered(lambda sub: sub.id != upcoming_subscription.id)
            for sub in remaining_subscriptions:
                if upcoming_subscription.actual_start_date <= sub.end_date and sub.actual_start_date <= upcoming_subscription.end_date and sub not in donot_consider_subs:
                    overlapping_subscription |= sub
            if overlapping_subscription:
                if upcoming_subscription.state == 'paid':
                    if all(sub.state == 'paid' for sub in overlapping_subscription):
                        donot_consider_subs |= upcoming_subscription
                        for overlapping_sub in overlapping_subscription:
                            if overlapping_sub != overlapping_subscription[-1]:
                                donot_consider_subs |= overlapping_sub
                        continue
                    elif any(sub.state == 'in_progress' for sub in overlapping_subscription):
                        donot_consider_subs |= upcoming_subscription
                        for overlapping_sub in overlapping_subscription:
                            if overlapping_sub.state != 'in_progress':
                                donot_consider_subs |= overlapping_sub
                        continue
            if this_new_end_date < upcoming_subscription.actual_start_date:
                break
            if not upcoming_subscription.is_subscription_moved:
                upcoming_subscription.write({
                    'is_subscription_moved': True,
                    'previous_start_date': upcoming_subscription.actual_start_date
                })
            upcoming_sub_current_start_date = upcoming_subscription.actual_start_date
            upcoming_sub_new_start_date = upcoming_subscription.get_new_start_date(this_new_end_date + timedelta(days=1))
            calendar_ids_to_delete = upcoming_subscription.meal_calendar_ids.filtered(
                lambda cal: upcoming_sub_current_start_date <= cal.date < upcoming_sub_new_start_date
            )
            delivery_days = len(list(set(calendar_ids_to_delete.filtered(lambda cal: cal.state in ['active', 'active_with_meal']).mapped('date'))))
            calendar_ids_to_delete.sudo().unlink()
            # find end date
            upcoming_subscription_end_date = upcoming_subscription.end_date
            day = 0
            calendar_date = upcoming_subscription_end_date + timedelta(days=1)
            if delivery_days == 0:
                excluded_weekdays = []
                if not upcoming_subscription.monday:
                    excluded_weekdays.append(0)
                if not upcoming_subscription.tuesday:
                    excluded_weekdays.append(1)
                if not upcoming_subscription.wednesday:
                    excluded_weekdays.append(2)
                if not upcoming_subscription.thursday:
                    excluded_weekdays.append(3)
                if not upcoming_subscription.friday:
                    excluded_weekdays.append(4)
                if not upcoming_subscription.saturday:
                    excluded_weekdays.append(5)
                if not upcoming_subscription.sunday:
                    excluded_weekdays.append(6)
                calendar_date = upcoming_subscription._get_end_date(excluded_weekdays, upcoming_subscription.plan_choice_id.no_of_day, upcoming_sub_new_start_date) + timedelta(days=1)
                
            while day < delivery_days:
                day_of_date = str(calendar_date.weekday())
                day_shifts = upcoming_subscription.partner_id.shift_ids.filtered(lambda shift:
                    shift.period=='day_of_week'
                )
                schedule_line = False
                shift = False
                address = False
                if not schedule_line:
                    schedule_line = day_shifts.filtered(lambda shift:
                        shift.day_of_week == 'day_of_date'
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    range_shifts = upcoming_subscription.partner_id.shift_ids.filtered(lambda shift:
                        shift.period=='date_range'
                    )
                    schedule_line = range_shifts.filtered(lambda shift:
                        shift.from_date <= calendar_date <= shift.to_date
                    )
                    shift = schedule_line.shift_type if schedule_line else False
                    address = schedule_line.address_id if schedule_line else False
                if not schedule_line:
                    shift = upcoming_subscription.partner_id.customer_address_id.shift_id if upcoming_subscription.partner_id.customer_address_id else False
                    address = upcoming_subscription.partner_id.customer_address_id
                available_meal = upcoming_subscription.meal_count_ids
                meal_category_ids=[]
                for record in available_meal:
                    if record.additional_count > 0:
                        category_ids=record.meal_category_id.ids
                        meal_category_ids.append(category_ids[0])
                is_off_day = upcoming_subscription.check_off_day(calendar_date)
                if is_off_day:
                    self.env['customer.meal.calendar'].create({
                        "date": calendar_date,
                        "partner_id": upcoming_subscription.partner_id.id,
                        "so_id": upcoming_subscription.id,
                        "state" :'off_day',
                        "off_day" : is_off_day,
                    })
                else:
                    for i in meal_category_ids:
                        meal_count = upcoming_subscription.meal_count_ids.filtered(lambda meal: meal.meal_category_id.id == i)
                        for j in range(int(meal_count.additional_count)):
                            # for line in upcoming_subscription.plan_id.meal_config_ids:
                            #     if line.meal_category_id.id == i:
                            #         deafult_meal_id = line.meal_ids[0].id if line.meal_ids else False
                            #         break
                            meal_calendar = self.env['customer.meal.calendar'].create({
                                "date": calendar_date,
                                "partner_id": upcoming_subscription.partner_id.id,
                                "so_id": upcoming_subscription.id,
                                "meal_category_id":i,
                                "plan_category_id": upcoming_subscription.plan_category_id.id,
                                "shift_id" : shift.id if shift else False,
                                "address_id" : address.id if address else False,
                            })
                            meal_calendar._onchange_state()
                            upcoming_subscription.apply_default_meals_by_date_range(calendar_date, calendar_date)
                    day += 1
                calendar_date += timedelta(days=1)
            upcoming_subscription.with_context(skip_subscription_overlap_check=True).write({
                'actual_start_date': upcoming_sub_new_start_date,
                'end_date': calendar_date - timedelta(days=1),
            })
            upcoming_subscription.with_context(skip_base_price_calculation=True)._compute_amount()
            this_new_end_date = upcoming_subscription.end_date

    def unfreeze_subscription_day(self, unfreeze_date):
        if not self:
            raise ValidationError(_("Subcription not passed."))
        if not unfreeze_date:
            raise ValidationError(_("Un-Freeze date not passed."))
        off_days = []
        if not self.sunday:
            off_days.append(6)
        if not self.monday:
            off_days.append(0)
        if not self.tuesday:
            off_days.append(1)
        if not self.wednesday:
            off_days.append(2)
        if not self.thursday:
            off_days.append(3)
        if not self.friday:
            off_days.append(4)
        if not self.saturday:
            off_days.append(5)
        if unfreeze_date.weekday() in off_days:
            raise ValidationError(_(f"{unfreeze_date.strftime('%b %d, %Y')} is an off day in the given subscription."))
        calendar_ids = self.env['customer.meal.calendar'].search([
            ('date', '=', unfreeze_date),
            ('so_id', '=', self.id),
            ('state', '=', 'freezed')
        ])
        if not calendar_ids:
            raise ValidationError(_(f"Nothing to unfreeze on {unfreeze_date.strftime('%b %d, %Y')}"))
        for calendar in calendar_ids:
            calendar.state = 'active_with_meal'
            calendar._onchange_state()
        current_last_day_calendar_ids = self.env['customer.meal.calendar'].search([
            ('date', '=', self.end_date),
            ('so_id', '=', self.id)
        ])
        new_end_date = self.end_date - timedelta(days=1)
        next_last_day_calendar_ids = self.env['customer.meal.calendar'].search([
            ('date', '=', new_end_date),
            ('so_id', '=', self.id)
        ])
        last_day_state = next_last_day_calendar_ids.mapped('state')
        last_day_calendar_ids = self.env['customer.meal.calendar']
        while 'off_day' in last_day_state:
            last_day_calendar_ids |= next_last_day_calendar_ids
            new_end_date = new_end_date - timedelta(days=1)
            next_last_day_calendar_ids = self.env['customer.meal.calendar'].search([
                ('date', '=', new_end_date),
                ('so_id', '=', self.id),
            ])
            last_day_state = next_last_day_calendar_ids.mapped('state')
        while 'freezed' in last_day_state:
            last_day_calendar_ids |= next_last_day_calendar_ids
            new_end_date = new_end_date - timedelta(days=1)
            next_last_day_calendar_ids = self.env['customer.meal.calendar'].search([
                ('date', '=', new_end_date),
                ('so_id', '=', self.id),
            ])
            last_day_state = next_last_day_calendar_ids.mapped('state')
        last_day_calendar_ids |= current_last_day_calendar_ids
        last_day_calendar_ids.unlink()
        self.end_date = new_end_date
        self.with_context(skip_base_price_calculation=True)._compute_amount()

        # move backwards any moved subscriptions
        previous_plan_end_date = new_end_date
        upcoming_subscriptions = self.env['diet.subscription.order'].search([
            ('partner_id', '=', self.partner_id.id),
            ('id', '!=', self.id),
            ('state', 'in', ['in_progress']),
            ('actual_start_date', '>=', unfreeze_date),
            ('is_subscription_moved', '=', True)
        ])
        for upcoming_subscription in upcoming_subscriptions:
            upcoming_subs_current_start_date = upcoming_subscription.actual_start_date
            upcoming_subs_new_start_date = upcoming_subscription.actual_start_date - timedelta(days=1)
            if upcoming_subscription.meal_calendar_ids:
                if upcoming_subs_new_start_date < previous_plan_end_date:
                    upcoming_subs_new_start_date = previous_plan_end_date
                elif upcoming_subs_new_start_date < upcoming_subscription.previous_start_date:
                    upcoming_subs_new_start_date = upcoming_subscription.previous_start_date
                elif upcoming_subs_new_start_date.weekday() in off_days:
                    upcoming_subs_new_start_date = upcoming_subscription.get_new_start_date(upcoming_subs_new_start_date)
                    day_delta = 2
                    while (upcoming_subs_new_start_date == upcoming_subs_current_start_date):
                        upcoming_subs_new_start_date = upcoming_subscription.get_new_start_date(upcoming_subs_new_start_date - timedelta(days=day_delta))
                        day_delta += 1
                gen_end_date = upcoming_subs_current_start_date - timedelta(days=1)
                if gen_end_date < upcoming_subs_new_start_date:
                    gen_end_date = upcoming_subs_new_start_date
                upcoming_subscription.generate_meal_calendar_by_date_range(upcoming_subs_new_start_date, gen_end_date)
                days_to_create_count = 0
                date_temp = upcoming_subs_new_start_date
                if date_temp == upcoming_subscription.previous_start_date:
                    days_to_create_count = 1
                else:
                    while date_temp < upcoming_subs_current_start_date:
                        if date_temp.weekday() not in off_days:
                            days_to_create_count += 1
                        date_temp += timedelta(days=1)
                upcoming_subscription_current_end_date = upcoming_subscription.end_date
                day_delete_index = days_to_create_count
                while day_delete_index > 0:
                    current_last_day_calendar_ids = self.env['customer.meal.calendar'].search([
                        ('date', '=', upcoming_subscription.end_date),
                        ('so_id', '=', upcoming_subscription.id)
                    ])
                    new_end_date = upcoming_subscription.end_date - timedelta(days=1)
                    next_last_day_calendar_ids = self.env['customer.meal.calendar'].search([
                        ('date', '=', new_end_date),
                        ('so_id', '=', upcoming_subscription.id)
                    ])
                    last_day_state = next_last_day_calendar_ids.mapped('state')
                    last_day_calendar_ids = self.env['customer.meal.calendar']
                    while 'off_day' in last_day_state:
                        last_day_calendar_ids |= next_last_day_calendar_ids
                        new_end_date = new_end_date - timedelta(days=1)
                        next_last_day_calendar_ids = self.env['customer.meal.calendar'].search([
                            ('date', '=', new_end_date),
                            ('so_id', '=', upcoming_subscription.id),
                        ])
                        last_day_state = next_last_day_calendar_ids.mapped('state')
                    last_day_calendar_ids |= current_last_day_calendar_ids
                    last_day_calendar_ids.unlink()
                    day_delete_index -= 1
            else:
                upcoming_subs_off_days = []
                if not upcoming_subscription.sunday:
                    upcoming_subs_off_days.append(6)
                if not upcoming_subscription.monday:
                    upcoming_subs_off_days.append(0)
                if not upcoming_subscription.tuesday:
                    upcoming_subs_off_days.append(1)
                if not upcoming_subscription.wednesday:
                    upcoming_subs_off_days.append(2)
                if not upcoming_subscription.thursday:
                    upcoming_subs_off_days.append(3)
                if not upcoming_subscription.friday:
                    upcoming_subs_off_days.append(4)
                if not upcoming_subscription.saturday:
                    upcoming_subs_off_days.append(5)
                new_end_date =  upcoming_subscription._get_end_date(upcoming_subs_off_days, upcoming_subscription.plan_choice_id.no_of_day, upcoming_subs_new_start_date)
            upcoming_subscription.with_context(skip_subscription_overlap_check=True).write({
                'actual_start_date': upcoming_subs_new_start_date,
                'end_date': new_end_date
            })
            upcoming_subscription.with_context(skip_base_price_calculation=True)._compute_amount()

    def reverse_subscription_ramdan(self):
        """
        Reverse the changes made to a single subscription by process_subscription_ramdan
        """
        processed_subs = []
        for subscription in self.filtered(lambda subs: subs.ramdan_plan_applied and not subs.plan_id.is_ramdan_plan):
            ramdan_start_date = self.env.company.ramdan_start_date
            ramdan_end_date = self.env.company.ramdan_end_date
            
            if not ramdan_start_date or not ramdan_end_date:
                raise UserError(_("Ramdan date range not configured."))
                
            # 1. Delete all meal calendar entries created by the Ramdan plan for the date range
            ramdan_calendar_entries = subscription.meal_calendar_ids.filtered(
                lambda cal: cal.date >= ramdan_start_date 
                and cal.date <= ramdan_end_date
                and not cal.driver_order_id  # Don't delete entries already delivered
            )
            
            # Save dates to regenerate regular meal calendars for
            date_to_regenerate = []
            for entry in ramdan_calendar_entries:
                if entry.date not in date_to_regenerate:
                    date_to_regenerate.append(entry.date)
            
            # Delete ramdan entries
            if ramdan_calendar_entries:
                ramdan_calendar_entries.sudo().unlink()
            
            # 2. Reset subscription to original plan values
            subscription.write({
                'ramdan_plan_id': False,
                'ramdan_plan_choice_id': False,
                'ramdan_plan_applied': False
            })
            
            # 3. Regenerate regular meal calendars for the affected dates
            for regen_date in date_to_regenerate:
                subscription.generate_meal_calendar_by_date_range(regen_date, regen_date)
            
            self.env.cr.execute(f"""
                UPDATE sale_order 
                SET note = CONCAT(COALESCE(note, ''), '\nUn-processed by {self.env.user.name} custom action on {fields.Datetime.now().strftime("%d-%m-%Y %H:%M:%S")}') 
                WHERE id = {subscription.id}
            """)
            
            processed_subs.append(subscription.order_number)
        
        # For form view button (single record), just return True
        if len(processed_subs) == 1 and self.env.context.get('from_button'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f"Successfully processed order {processed_subs[0]}",
                    'sticky': False,
                    'type': 'success',
                }
            }
        
        # For server action (multiple records), show summary message
        if processed_subs:
            message = f"Successfully processed {len(processed_subs)} orders: {', '.join(processed_subs)}"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': message,
                    'sticky': False,
                    'type': 'success',
                }
            }
        
        return True
        

    def edit_subscription(self):
        if self.plan_id and self.ramdan_plan_id and self.plan_id.is_ramdan_plan and self.ramdan_plan_id.is_ramdan_plan:
            raise ValidationError(_("Plan and Alternate Plan cannot be of the same type. Choose either one as 'Ramdan' or vice versa."))
        if self.plan_id and self.ramdan_plan_id and not self.plan_id.is_ramdan_plan and not self.ramdan_plan_id.is_ramdan_plan:
            raise ValidationError(_("Plan and Alternate Plan cannot be of the same type. Choose either one as 'Ramdan' or vice versa."))
        for record in self:
            if record.package_days == 1 and not self.env.user.has_group('diet.group_subscription_extension'):
                plan_name = record.plan_choice_id.name if record.plan_choice_id else "unknown plan"
                raise ValidationError(_(
                    "You cannot edit a subscription for the '%s' plan."
                ) % plan_name)  
        base_meal_config = []
        additional_meal_config = []
        if not self.plan_id.is_ramdan_plan:
            plan = self.plan_id
            meal_config = self.meal_count_ids
        elif not self.ramdan_plan_id.is_ramdan_plan:
            plan = self.ramdan_plan_id
            meal_config = self.ramdan_meal_count_ids
        else:
            plan = self.plan_id
            meal_config = self.meal_count_ids

        for categ_line in meal_config:
            if categ_line.meal_category_id in plan.meal_config_ids.mapped('meal_category_id') and not categ_line.additional_meal:
                base_meal_count = plan.meal_config_ids.filtered(lambda meal_conf: meal_conf.meal_category_id == categ_line.meal_category_id).meal_count
                additional_price = plan.meal_config_ids.filtered(lambda meal_conf: meal_conf.meal_category_id == categ_line.meal_category_id).additional_price
                base_meal_config.append((0, 0, {
                    "meal_category_id": categ_line.meal_category_id.id,
                    "base_meal_count": base_meal_count,
                    "additional_price": additional_price,
                    "additional_count": categ_line.additional_count,
                    "subscription_config_line_id": categ_line.id
                }))
            if categ_line.meal_category_id in plan.additional_meal_config_ids.mapped('meal_category_id'):
                additional_meal_config.append((0, 0, {
                    "meal_category_id": categ_line.meal_category_id.id,
                    "meal_count": categ_line.additional_count,
                    "subscription_config_line_id": categ_line.id
                }))
            if categ_line.additional_meal and categ_line.meal_category_id not in plan.additional_meal_config_ids.mapped('meal_category_id'):
                additional_meal_config.append((0, 0, {
                    "meal_category_id": categ_line.meal_category_id.id,
                    "meal_count": categ_line.additional_count,
                    "subscription_config_line_id": categ_line.id
                }))
        return {
            "name": _("Edit Subscription"),
            "type": "ir.actions.act_window",
            "res_model": "subscription.edit.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_subscription_id": self.id,
                "default_sunday": self.sunday,
                "default_monday": self.monday,
                "default_tuesday": self.tuesday,
                "default_wednesday": self.wednesday,
                "default_thursday": self.thursday,
                "default_friday": self.friday,
                "default_saturday": self.saturday,
                "default_start_date": self.actual_start_date if fields.Date.today()+timedelta(days=2) < self.actual_start_date else fields.Date.today()+timedelta(days=2),
                "default_end_date": self.end_date,
                "default_protein": self.protein,
                "default_carbohydrates": self.carbs,
                "default_subscription_edit_wizard_line_ids": base_meal_config,
                "default_subscription_edit_wizard_additional_line_ids": additional_meal_config
            }
        }
    
    def edit_ramdan_subscription(self):
        if self.plan_id and self.ramdan_plan_id and self.plan_id.is_ramdan_plan and self.ramdan_plan_id.is_ramdan_plan:
            raise ValidationError(_("Plan and Alternate Plan cannot be of the same type. Choose either one as 'Ramdan' or vice versa."))
        if self.plan_id and self.ramdan_plan_id and not self.plan_id.is_ramdan_plan and not self.ramdan_plan_id.is_ramdan_plan:
            raise ValidationError(_("Plan and Alternate Plan cannot be of the same type. Choose either one as 'Ramdan' or vice versa."))
        ramdan_start_date = self.env.company.ramdan_start_date
        ramdan_end_date = self.env.company.ramdan_end_date
        if ramdan_start_date and self.actual_start_date < ramdan_start_date:
            start_date = ramdan_start_date
        elif ramdan_start_date and self.actual_start_date > ramdan_start_date:
            start_date = self.actual_start_date
        else:
            start_date = fields.Date.today() + timedelta(days=2)
        if  ramdan_end_date and self.end_date > ramdan_end_date:
            end_date = ramdan_end_date
        elif ramdan_end_date and self.end_date <= ramdan_end_date:
            end_date = self.end_date
        else: 
            end_date = self.end_date
        lines = []
        if self.ramdan_plan_id.is_ramdan_plan:
            ramdan_meal_config = self.ramdan_meal_count_ids
        elif self.plan_id.is_ramdan_plan:
            ramdan_meal_config = self.meal_count_ids
        else:
            ramdan_meal_config = self.meal_count_ids
        for sl in ramdan_meal_config:
            lines.append((0, 0, {
                "meal_category_id": sl.meal_category_id.id,
                "meal_count": sl.additional_count,
                "subscription_config_line_id": sl.id
            }))
        return {
            "name": _("Edit Ramadan Subscription"),
            "type": "ir.actions.act_window",
            "res_model": "ramdan.subscription.edit.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_subscription_id": self.id,
                "default_start_date": start_date,
                "default_end_date": end_date,
                "default_ramdan_subscription_edit_line_ids": lines,
                "default_sunday": self.sunday,
                "default_monday": self.monday,
                "default_tuesday": self.tuesday,
                "default_wednesday": self.wednesday,
                "default_thursday": self.thursday,
                "default_friday": self.friday,
                "default_saturday": self.saturday,
                "default_protein": self.protein,
                "default_carbohydrates": self.carbs,
            }
        }
    
    def change_start_date(self):
        user_tz = self.env.context.get('tz') or self.env.company.partner_id.tz or 'UTC'
        user_timezone = timezone(user_tz)                
        current_datetime = datetime.now(user_timezone)
        time_430_am = time(4, 30)
        now = current_datetime.time()
        today = current_datetime.date()
        if now > time_430_am and self.actual_start_date - today < timedelta(days=2):
            raise ValidationError(_("You can only change the start date 2 days before the actual start date."))
        for record in self:
            if record.package_days == 1 and not self.env.user.has_group('diet.group_subscription_extension'):
                plan_name = record.plan_choice_id.name if record.plan_choice_id else "unknown plan"
                raise ValidationError(_(
                    "You cannot change the start date for the '%s' plan."
                ) % plan_name)  
        return {
            "name": _("Change Start Date"),
            "type": "ir.actions.act_window",
            "res_model": "subscription.start.date.edit.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_subscription_id": self.id,
                "default_start_date": self.actual_start_date,
                "default_end_date": self.end_date
            }
        }

    def change_subscription_start_date(self, new_start_date, new_end_date):
        if not new_start_date:
            raise ValidationError(_("Start date not passed."))
        current_end_date = self.end_date
        if self.meal_calendar_ids:
            self.meal_calendar_ids.unlink()
            self.generate_meal_calendar_by_date_range(new_start_date, new_end_date)
        self.with_context(skip_subscription_overlap_check=True).write({
            'actual_start_date': new_start_date,
            'end_date': new_end_date
        })
        self.with_context(skip_base_price_calculation=True)._compute_amount()
        this_new_end_date = self.end_date
        upcoming_subscriptions = self.env['diet.subscription.order'].search([
            ('partner_id', '=', self.partner_id.id),
            ('id', '!=', self.id),
            ('state', 'in', ['in_progress']),
            ('actual_start_date', '>=', current_end_date),
        ])
        for upcoming_subscription in upcoming_subscriptions:
            if this_new_end_date < upcoming_subscription.actual_start_date:
                break
            if not upcoming_subscription.is_subscription_moved:
                upcoming_subscription.write({
                    'is_subscription_moved': True,
                    'previous_start_date': upcoming_subscription.actual_start_date
                })
            this_new_start_date = upcoming_subscription.get_new_start_date(this_new_end_date + timedelta(days=1))
            difference = (this_new_start_date - upcoming_subscription.actual_start_date).days
            calendar_ids_to_delete = upcoming_subscription.meal_calendar_ids.filtered(
                lambda cal: upcoming_subscription.actual_start_date <= cal.date < this_new_start_date
            )
            calendar_ids_to_delete.sudo().unlink()
            this_new_end_date = upcoming_subscription.end_date + timedelta(days=difference)
            upcoming_subscription.generate_meal_calendar_by_date_range(upcoming_subscription.end_date + timedelta(days=1), this_new_end_date)
            upcoming_subscription.with_context(skip_subscription_overlap_check=True).write({
                'actual_start_date': this_new_start_date,
                'end_date': this_new_end_date
            })
            upcoming_subscription.with_context(skip_base_price_calculation=True)._compute_amount()


class SubscriptionAdditonalMeals(models.Model):
    _name = 'subscription.additional.meals'
    _description = 'Subscription Additional Meals'

    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription', required=True, ondelete='cascade')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category', required=True)
    count = fields.Integer(string='Meal Count', required=True, default=0)
    meal_id = fields.Many2one('product.product', string='Meal')
    price = fields.Float(string='Price', store=True)