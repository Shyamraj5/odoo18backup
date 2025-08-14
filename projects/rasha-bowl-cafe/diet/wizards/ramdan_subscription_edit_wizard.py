from odoo import models, fields, api, _
from odoo.exceptions import UserError

class RamdanSubscriptionEditWizard(models.TransientModel):
    _name = 'ramdan.subscription.edit.wizard'
    _description = 'Ramdan Subscription Edit Wizard'

    subscription_id = fields.Many2one('diet.subscription.order', string='Subscription')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    currency_id = fields.Many2one('res.currency', string='Currency', related='subscription_id.currency_id')
    additional_amount = fields.Monetary(string='Additional Charge')
    ramdan_subscription_edit_line_ids = fields.One2many('ramdan.subscription.edit.line', 'wizard_id', string='Ramdan Subscription Edit Lines')
    ramdan_subscription_edit_additional_line_ids = fields.One2many('ramdan.subscription.edit.line.additional', 'wizard_id', string='Ramdan Subscription Edit Additional Lines')
    protein = fields.Integer('Protein')
    carbohydrates = fields.Integer('Carbohydrates')
    sunday = fields.Boolean('Sunday')
    monday = fields.Boolean('Monday')
    tuesday = fields.Boolean('Tuesday')
    wednesday = fields.Boolean('Wednesday')
    thursday = fields.Boolean('Thursday')
    friday = fields.Boolean('Friday')
    saturday = fields.Boolean('Saturday')

    def action_submit(self):
        config_update_report = ""
        for line in self.ramdan_subscription_edit_line_ids.filtered(lambda l: l.meal_count != l.subscription_config_line_id.additional_count):
            config_update_report += f"{line.meal_category_id.name}: {line.subscription_config_line_id.additional_count} --> {line.meal_count}\n"
        calendar_entries = self.env['customer.meal.calendar'].search([
            ('so_id', '=', self.subscription_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('state', 'in', ['active', 'active_with_meal', 'off_day'])
        ])
        calendar_entries_dates = sorted(list(set(list(calendar_entries.mapped('date')))))
        calendar_entries.unlink()
        self.subscription_id.write({
            'protein': self.protein,
            'carbs': self.carbohydrates,
            'sunday': self.sunday,
            'monday': self.monday,
            'tuesday': self.tuesday,
            'wednesday': self.wednesday,
            'thursday': self.thursday,
            'friday': self.friday,
            'saturday': self.saturday,
        })
        if self.subscription_id.ramdan_plan_id.is_ramdan_plan:
            ramdan_meal_config = self.subscription_id.ramdan_meal_count_ids
        elif self.subscription_id.plan_id.is_ramdan_plan:
            ramdan_meal_config = self.subscription_id.meal_count_ids
        else:
            ramdan_meal_config = self.subscription_id.meal_count_ids
        for line in self.ramdan_subscription_edit_line_ids:
            subs_meal_line = ramdan_meal_config.filtered(lambda meal_line: meal_line.meal_category_id == line.meal_category_id)
            if subs_meal_line:
                subs_meal_line.additional_count = line.meal_count
            else:
                ramdan_meal_config = [(0,0,{
                    "meal_category_id": line.meal_category_id.id,
                    "additional_count": line.meal_count
                })]
        for line in self.ramdan_subscription_edit_additional_line_ids:
            subs_meal_line = ramdan_meal_config.filtered(lambda meal_line: meal_line.meal_category_id == line.meal_category_id)
            if subs_meal_line:
                subs_meal_line.additional_count = line.meal_count
            else:
                ramdan_meal_config = [(0,0,{
                    "meal_category_id": line.meal_category_id.id,
                    "additional_count": line.meal_count
                })]
        if self.additional_amount:
            self.subscription_id.manual_price += self.additional_amount
        for cal_date in calendar_entries_dates:
            if self.subscription_id.ramdan_plan_id.is_ramdan_plan:
                self.subscription_id.generate_meal_calendar_ramdan(cal_date, cal_date)
            elif self.subscription_id.plan_id.is_ramdan_plan:
                self.subscription_id.generate_meal_calendar_by_date_range(cal_date, cal_date)
            else:
                self.subscription_id.generate_meal_calendar_by_date_range(cal_date, cal_date)
        self.subscription_id.message_post(body=_(
            f"Subscription Edited for Ramdan from {self.start_date} to {self.end_date}\n"\
            + f"Additional Amount: {self.additional_amount}\n"\
            + f"Meal Count Edited: \n"\
            + f"\n{config_update_report}"
        ))

    @api.constrains('start_date')
    def _constrains_start_date(self):
        if self.start_date and self.env.company.ramdan_start_date and self.start_date < self.env.company.ramdan_start_date:
            raise UserError(_('Start Date should be atleast greater than or equal to Ramdan Start Date.'))
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise UserError(_('Start Date should be less than or equal to End Date.'))
        if self.start_date and self.subscription_id.actual_start_date and self.start_date < self.subscription_id.actual_start_date:
            raise UserError(_('Start Date should be atleast greater than or equal to Subscription Start Date.'))
        if self.start_date and self.subscription_id.end_date and self.start_date > self.subscription_id.end_date:
            raise UserError(_('Start Date should be less than or equal to Subscription End Date.'))



class RamdanSubscriptionEditLine(models.TransientModel):
    _name = 'ramdan.subscription.edit.line'
    _description = 'Ramdan Subscription Edit Line'

    wizard_id = fields.Many2one('ramdan.subscription.edit.wizard', string='Wizard')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    meal_count = fields.Integer('Meal Count')
    subscription_config_line_id = fields.Many2one('meals.count', string='Subscription Meal Config Line')

class RamdanSubscriptionEditLineAdditional(models.TransientModel):
    _name = 'ramdan.subscription.edit.line.additional'
    _description = 'Ramdan Subscription Edit Line Additional'

    wizard_id = fields.Many2one('ramdan.subscription.edit.wizard', string='Wizard')
    meal_category_ids = fields.Many2many('meals.category', string='Meal Category', compute='_compute_meal_category_ids')
    meal_category_id = fields.Many2one('meals.category', string='Meal Category')
    meal_count = fields.Integer('Meal Count')

    @api.depends('wizard_id.ramdan_subscription_edit_line_ids', 'wizard_id.ramdan_subscription_edit_line_ids.meal_category_id')
    def _compute_meal_category_ids(self):
        for record in self:
            record.meal_category_ids = record.wizard_id.ramdan_subscription_edit_line_ids.mapped('meal_category_id')
            