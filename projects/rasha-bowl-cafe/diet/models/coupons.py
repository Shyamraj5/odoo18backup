from uuid import uuid4

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError

class CouponProgram(models.Model):
    _name = 'coupon.program'
    _description = 'Coupon Program'
    _rec_name = 'program_name'
    
    program_code = fields.Char('Program Code')
    program_name = fields.Char('Program Name')
    program_discount = fields.Float('Discount')
    coupon_count = fields.Integer('Coupon Count')
    generated_coupon_count = fields.Integer('Generated Coupons Count', compute='compute_generated_coupon_count')
    start_date = fields.Date('Start Date')
    program_expiry = fields.Date('End Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ], string='Status', default='draft')
    program_type = fields.Selection([
        ('promocode', 'Promo Code'),
        ('coupon', 'Coupons')
    ], string='Program Type', default='promocode')
    promocode_used = fields.Integer('Promo Code Used', compute='_compute_promocode_used', store=True)
    participation_ids = fields.One2many('program.participated.customers', 'program_id', string='Participation')
    discount_type = fields.Selection([('fix','Fixed'),('percentage','Percentage')], default="fix")
    sunday = fields.Boolean(string="Sunday")
    monday = fields.Boolean(string="Monday")
    tuesday = fields.Boolean(string="Tuesday")
    wednesday = fields.Boolean(string="Wednesday")
    thursday = fields.Boolean(string="Thursday")
    friday = fields.Boolean(string="Friday")
    saturday = fields.Boolean(string="Saturday")
    program_availability = fields.Selection([('alldays','All Days'),('custom','Custom')], default='alldays', string="Program Availability")
    plan_applicable_ids = fields.One2many('program.applicable.plans', 'program_id', string="plans")
    is_universal_code = fields.Boolean('Is Universal Code', default=True)
    no_partner_limit = fields.Boolean('No Parter Limit', default=False)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['program_code'] = self.env['ir.sequence'].next_by_code('coupon.program.sequence')
        return super().create(vals_list)

    def compute_generated_coupon_count(self):
        for rec in self:
            coupons = self.env['coupon.program.code'].search([
                ('coupon_program_id','=',rec.id)
            ])
            rec.generated_coupon_count = len(coupons)

    def generate_coupons(self):
        for rec in self:
            for i in range(0, rec.coupon_count):
                self.env['coupon.program.code'].create({
                    'coupon_program_id': rec.id,
                    'coupon_code': '044' + str(uuid4())[7:-18]
                })

    def confirm(self):
        for program in self:
            if program.program_type == 'coupon':
                self.generate_coupons()
            self.state = 'active'
    
    @api.depends('participation_ids')
    def _compute_promocode_used(self):
        for program in self:
            program.promocode_used = len(program.participation_ids)

    def view_coupons(self):
        return {
            'name': _("Coupons"),
            'type': 'ir.actions.act_window',
            'res_model': 'coupon.program.code',
            'domain': [('coupon_program_id','=',self.id)],
            'view_mode': 'list',
            'target': 'current'
        }
    
    @api.constrains('program_discount', 'is_universal_code', 'plan_applicable_ids.program_discount')
    def _constrains_program_discount(self):
        for program in self:
            if program.is_universal_code and not program.program_discount:
                raise ValidationError(_("Discount cannot be zero."))
            
    def expire(self):
        for program in self:
            program.write({
                'state': 'expired'
            })
    
    def draft(self):
        for program in self:
            program.write({
                'state': 'draft'
            })
    

class CouponProgramCode(models.Model):
    _name = 'coupon.program.code'
    _description = 'Coupon Program Code'
    
    coupon_program_id = fields.Many2one('coupon.program', string='Coupon Program')
    coupon_code = fields.Char('Coupon Code')
    state = fields.Selection([
        ('unused', 'Un-Used'),
        ('used', 'Used')
    ], string='Status', default='unused')

    def name_get(self):
        return [(coupon.id, f'{coupon.coupon_program_id.name}: {coupon.coupon_code}') for coupon in self]

    _sql_constraints = [
        ('coupon_code_unique', 'UNIQUE(coupon_code)', 'A coupon must have a unique code.')
    ]

class ProgramParticipatedCustomers(models.Model):
    _name = 'program.participated.customers'
    _description = 'Program Participated Customers'
    
    program_id = fields.Many2one('coupon.program', string='Program')
    customer_id = fields.Many2one('res.partner', string='Customer')
    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    applied_code = fields.Char('Applied Code')
    applied_date = fields.Datetime('Applied Date', default=fields.Datetime.now())


class ProgramApplicablePlans(models.Model):
    _name = 'program.applicable.plans'
    _description = 'Program Applicable Plans'

    program_id = fields.Many2one('coupon.program', string="program")
    appl_plans_id = fields.Many2one('subscription.package.plan', string="Plans")
    appl_choice_ids = fields.Many2many('plan.choice', 'applicable_plan_line_id', 'choice_id',  string="Choice")
    available_plan_choice_ids = fields.Many2many('plan.choice', 'available_plan_line_id', 'available_choice_id', compute='_compute_available_plan_choice_ids')
    discount_type = fields.Selection([('fix','Fixed'),('percentage','Percentage')], default="fix")
    program_discount = fields.Float('Discount')

    @api.depends('appl_plans_id')
    def _compute_available_plan_choice_ids(self):
        for subs in self:
            subs.available_plan_choice_ids = False
            if subs.appl_plans_id and subs.appl_plans_id.day_choice_ids:
                subs.available_plan_choice_ids = [
                    (4,choice.id) for choice in subs.appl_plans_id.day_choice_ids
                ]
    
    @api.constrains('program_discount', 'program_id.is_universal_code')
    def _constrains_program_discount(self):
        for line in self:
            if not line.program_id.is_universal_code and not line.program_discount:
                raise ValidationError(_("Discount cannot be zero."))
