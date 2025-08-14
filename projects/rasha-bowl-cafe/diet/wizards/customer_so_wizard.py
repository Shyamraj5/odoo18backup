from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import timedelta


class CustomerSoWizard(models.Model):
    _name = 'customer.so.wizard'
    _description = 'Customer So Wizard'

    
    order_number = fields.Char(string ="Order No")
    date = fields.Date(string ="Date", default=fields.Date.today())
    partner_id = fields.Many2one('res.partner', string ="Customer")
    plan_id = fields.Many2one('subscription.package.plan', string ="Plan", domain="[('plan_category_id','=',plan_category_id)]")
    start_date = fields.Date(string ="Start Date", default=fields.Date.today())
    end_date = fields.Date(string ="End Date", compute='_compute_end_date')
    actual_start_date = fields.Date(string ="Activation Date", compute ='_compute_activation_date')
    plan_status = fields.Char(string ="Plan Status")
    sales_person_id = fields.Many2one('res.users', string ="Sales Person")
    total = fields.Float(string ="Total")
    refund = fields.Float(string ="Refund")
    payment_status = fields.Char(string ="Payment Status")
    paid_amount = fields.Float(string ="Paid Amount")
    balance_amount = fields.Float(string ="Balance Amount")
    promo_code = fields.Char(string ="Promo-code")
    order_id = fields.Many2one('res.partner', string ="Order Id")
    choice_ids = fields.Many2many('subscription.plan.choice', string='Choices', compute='_compute_choice_ids')
    choice_id = fields.Many2one('subscription.plan.choice', string='Choice', domain="[('id', 'in', choice_ids)]")
    meal_line_ids = fields.One2many('customer.so.wizard.line', 'customer_so_id', string ="Meal Line")
    currency_id = fields.Many2one('res.currency', string='Currency', related='choice_id.currency_id')
    plan_base_price = fields.Monetary('Plan Base Price', currency_field="currency_id", compute='_compute_amount', store=True)
    addons_price = fields.Monetary('Addons Price', currency_field="currency_id", compute='_compute_amount', store=True)
    total_price = fields.Monetary('Total Price', currency_field="currency_id", compute='_compute_amount', store=True)
    plan_category_id = fields.Many2one('plan.category', string ="Plan Category")

    @api.depends('start_date')
    def _compute_activation_date(self):
        order_count = self.env['diet.subscription.order'].search([])
        count =len(order_count)
        order_capacity = self.env['ir.config_parameter'].sudo().get_param('diet.order_capacity')
        buffer = self.env['ir.config_parameter'].sudo().get_param('diet.buffer')
        if count < int(order_capacity):
            self.actual_start_date = self.start_date + timedelta(days=2)
        else:
            self.actual_start_date = self.start_date + timedelta(days=(2 + int(buffer)))

    
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
            rec.write({
                "choice_ids": choices_ids
            })

    @api.depends('actual_start_date', 'plan_id')
    def _compute_end_date(self):
        for rec in self:
            if rec.actual_start_date and rec.plan_id:
                end_date = rec.actual_start_date + relativedelta(days=rec.plan_id.duration_days)
            else:
                end_date = False
            rec.write({
                "end_date": end_date
            })


    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id:
            self.meal_line_ids.unlink()
            self.env["customer.so.wizard.line"]._create_meal_line(customer_so_id=self)

    @api.depends(
        'choice_id',
        'meal_line_ids.default_count',
        'meal_line_ids.count',
        'meal_line_ids.meal_category_id'
    )
    def _compute_amount(self):
        for rec in self:
            base_plan_price = rec.choice_id.price if rec.choice_id else 0
            addons_price = 0
            for line in rec.meal_line_ids:
                line_addons_price = 0
                price_factor = 0
                count_difference = line.count - line.default_count
                price_factor_line = rec.choice_id.meal_category_line_ids.filtered(lambda categ:
                    categ.meal_category_id == line.meal_category_id
                )
                if price_factor_line:
                    price_factor = price_factor_line.additional_add_price if (count_difference >= 0) else price_factor_line.additional_remove_price
                line_addons_price = count_difference * price_factor
                addons_price += line_addons_price
                
            rec.update({
                "plan_base_price": base_plan_price,
                "addons_price": addons_price,
                "total_price": base_plan_price + addons_price
            })

    def confirm(self):
        for rec in self:
            cal_date = rec.start_date
            while cal_date <= rec.end_date:
                self.env['customer.meal.calendar'].create({
                    "date": cal_date,
                    "partner_id": rec.partner_id.id
                })
                cal_date += timedelta(days=1)
            meal_lines = []
            for line in rec.meal_line_ids:
                meal_lines.append((0,0,{
                    "meal_category_id": line.meal_category_id.id,
                    "default_count": line.default_count,
                    "count": line.count,
                }))
            subscription_order_line_vals = {
                "plan_id": rec.plan_id.id,
                "start_date": rec.start_date,
                "end_date": rec.end_date,
                "choice_id": rec.choice_id.id,
                "meal_line_ids": meal_lines,
                "actual_start_date" : rec.actual_start_date,
                "partner_id" : rec.partner_id.id
            }
            rec.partner_id.customer_sale_order_line_ids = [(0,0,subscription_order_line_vals)]
            subscription_order_id = self.env['diet.subscription.order'].search([('partner_id','=',rec.partner_id.id)], limit=1, order='create_date desc')
            # create invoice
            invoice_lines = [(0,0,{
                "name": f"{rec.plan_id.name} - {rec.choice_id.name}",
                "price_unit": self.total_price,
                "quantity": 1,
            })]
            invoice_vals = {
                "move_type": "out_invoice",
                "partner_id": rec.partner_id.id,
                "customer_so_line_id": subscription_order_id.id,
                "invoice_line_ids": invoice_lines
            }
            invoice_id = self.env['account.move'].create(invoice_vals)
            invoice_id.action_post()
            payment_id = self.env['account.payment'].create({
                "partner_id": rec.partner_id.id,
                "amount": invoice_id.amount_total
            })
            payment_id.action_post()
            line_id = self.env['account.move.line'].search([('move_name','=',payment_id.name),('amount_residual','<',0)],limit=1)
            if line_id.amount_residual < 0:
                invoice_id.js_assign_outstanding_line(line_id.id)

            return {
                "name": _("Subscription Invoice"),
                "type": "ir.actions.act_window",
                "res_model": "account.move",
                "res_id": invoice_id.id,
                "view_mode": "form",
                "target": "current"
            }
    
class CustomerSoWizardLine(models.Model):
    _name = "customer.so.wizard.line"
    _description = "Customer SO Wizard Line"

    customer_so_id = fields.Many2one('customer.so.wizard', string ="Customer Sale Order")
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    default_count = fields.Integer('Default Count')
    count = fields.Integer('Count')

    def _create_meal_line(self, customer_so_id):
        meals = customer_so_id.plan_id.plan_meal_ids
        for meal in meals:
            self.create(
                {
                'customer_so_id': customer_so_id.id,
                "meal_category_id": meal.meal_category_id.id,
                "default_count": meal.default_count,
                "count": meal.default_count,
                }
            )

    def add_meal(self):
        self.count += 1
        return {
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'customer.so.wizard',
            'res_id': self.customer_so_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


    def remove_meal(self):
        if self.count > 0:
            self.count -= 1
        return {
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'customer.so.wizard',
            'res_id': self.customer_so_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
