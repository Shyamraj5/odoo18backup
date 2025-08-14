from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

class CommissionPlan(models.Model):
    _name = 'commission.plan'
    _description = 'Commission Plan'

    name = fields.Char(string='Plan Name', required=True)
    effective_period_start = fields.Date(string='Start Date', required=True)
    effective_period_end = fields.Date(string='End Date', required=True)
    payment_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Payment Frequency', default='monthly', required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('cancel', 'Cancelled')
        ],
        string="Status",
        default='draft',
        required=True
    )
    salesperson_ids = fields.One2many(
        'commission.plan.salesperson',
        'commission_plan_id',
        string='Sales People'
    )
    incentive_ids = fields.One2many(
        'commission.plan.incentive',
        'commission_plan_id',
        string='Incentives'
    )
    target_line_ids = fields.One2many('salesperson.target.line', 'commission_plan_salesperson_id', string='Target Lines')

    def action_approve(self):
        """Set the state to Approved."""
        for record in self:
            record.state = 'approved'

    def action_cancel(self):
        """Set the state to Cancelled."""
        for record in self:
            record.state = 'cancel'

    def action_draft(self):
        """Reset the state to Draft."""
        for record in self:
            record.state = 'draft'

    def action_view_incentives(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incentives',
            'res_model': 'incentive.bonus',
            'view_mode': 'list',
            'domain': [('commission_plan_id', '=', self.id)], 
            'target': 'new',
        }
    
class CommissionPlanSalesperson(models.Model):
    _name = 'commission.plan.salesperson'
    _description = 'Commission Plan Salesperson'

    commission_plan_id = fields.Many2one('commission.plan', string='Commission Plan', required=True, ondelete='cascade')
    salesperson_id = fields.Many2one('res.users', string='Salesperson', required=True, domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])
    target_line_ids = fields.One2many('salesperson.target.line', 'commission_plan_salesperson_id', string='Target Lines')
    is_target_set = fields.Boolean(string='Target Set', default=False)

    def action_view_details(self):
        """Automatically fetch `commission_plan_id` from the main form and open a form view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'commission.plan.salesperson',
            'view_mode': 'form',
            'res_id': self.id, 
            'target': 'new',
            'context': {
                'default_commission_plan_id': self.commission_plan_id.id,
                'default_salesperson_id': self.salesperson_id.id,
            },
        }
    
    def set_target(self):
        """Automatically fetch `commission_plan_id` from the main form and open a form view."""
        if self.commission_plan_id:
            start_date = self.commission_plan_id.effective_period_start
            end_date = self.commission_plan_id.effective_period_end
            payment_frequency = self.commission_plan_id.payment_frequency
            # Clear previous target lines
            self.target_line_ids = [(5, 0, 0)]
            self.is_target_set = True
            periods = []
            current_date = start_date.replace(day=1)

            if payment_frequency == 'monthly':
                while current_date <= end_date:
                    month_start = max(current_date, start_date)
                    next_month = current_date + relativedelta(months=1)
                    month_end = min(next_month - relativedelta(days=1), end_date)
                    periods.append({
                        'period_name': current_date.strftime('%Y %B'),
                        'start_date': month_start,
                        'end_date': month_end,
                    })
                    current_date = next_month

            elif payment_frequency == 'quarterly':
                while current_date <= end_date:
                    quarter_start = max(current_date, start_date)
                    next_quarter = current_date + relativedelta(months=3)
                    quarter_end = min(next_quarter - relativedelta(days=1), end_date)
                    periods.append({
                        'period_name': f"Q{((current_date.month - 1) // 3) + 1} {current_date.year}",
                        'start_date': quarter_start,
                        'end_date': quarter_end,
                    })
                    current_date = next_quarter

            elif payment_frequency == 'yearly':
                while current_date <= end_date:
                    year_start = max(current_date, start_date)
                    next_year = current_date + relativedelta(years=1)
                    year_end = min(next_year - relativedelta(days=1), end_date)
                    periods.append({
                        'period_name': current_date.strftime('%Y'),
                        'start_date': year_start,
                        'end_date': year_end,
                    })
                    current_date = next_year

            # Add new target lines based on periods
            lines = []
            for period in periods:
                lines.append({
                    'period_name': period['period_name'],
                    'start_date': period['start_date'],
                    'end_date': period['end_date'],
                    'target_amount': 0.0,
                    'commission_plan_salesperson_id': self.id
                })
            self.env['salesperson.target.line'].create(lines)
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'commission.plan.salesperson',
            'view_mode': 'form',
            'res_id': self.id, 
            'target': 'new',
            'context': {
                'default_commission_plan_id': self.commission_plan_id.id,
                'default_salesperson_id': self.salesperson_id.id,
            },
        }

class SalespersonTargetLine(models.Model):
    _name = 'salesperson.target.line'
    _description = 'Salesperson Target Line'

    period_name = fields.Char(string='Period', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    target_amount = fields.Float(string='Target Amount', required=True)
    commission_plan_salesperson_id = fields.Many2one('commission.plan.salesperson', string='Commission Plan Salesperson', required=True, ondelete='cascade')


class CommissionPlanIncentive(models.Model):
    _name = 'commission.plan.incentive'
    _description = 'Commission Plan Incentive'

    commission_plan_id = fields.Many2one('commission.plan', string='Commission Plan', required=True)
    target_completion = fields.Float(string='Target Completion (%)', required=True)
    commission_amount = fields.Float(string='Commission Amount', required=True)

