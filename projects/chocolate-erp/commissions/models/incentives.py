from odoo import models, fields, tools, api


class CommissionTracking(models.Model):
    _name = 'incentive.bonus'
    _description = 'Incentive Bonus'
    _auto = False
    _table = 'incentive_sql_view'
    
    commission_plan_id = fields.Many2one('commission.plan', string='Commission Plan', readonly=True)
    sales_person = fields.Many2one('res.users', string='Salesperson', readonly=True)
    total_sales_amount = fields.Float(string='Total Sales Amount', column_name='amount_total')
    date = fields.Date(string='Date', readonly=True)
    target_amount = fields.Float(string='Target')
    period_name = fields.Char('Period', readonly=True)
    incentive_bonus = fields.Float(string='Incentive Bonus', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW incentive_sql_view AS (
        SELECT
            ROW_NUMBER() OVER () AS id,
            cp.id AS commission_plan_id,
            ru.id AS sales_person,
            SUM(so.amount_untaxed) AS total_sales_amount,
            MAX(so.date_order)::date AS date,
            COALESCE((
                SELECT cpi.commission_amount
                FROM commission_plan_incentive cpi
                WHERE cpi.commission_plan_id = cp.id
                AND cpi.target_completion <= (
                    CASE
                        WHEN stl.target_amount > 0 THEN
                            (SUM(so.amount_untaxed) / stl.target_amount) * 100
                        ELSE 0
                    END
                )
                ORDER BY cpi.target_completion DESC
                LIMIT 1
            ), 0) AS incentive_bonus,
            stl.period_name,
            stl.target_amount,
            CASE
                WHEN cp.payment_frequency = 'monthly' THEN
                    (SUM(so.amount_untaxed) / COUNT(DISTINCT stl.period_name))
                WHEN cp.payment_frequency = 'quarterly' THEN
                    (SUM(so.amount_untaxed) / COUNT(DISTINCT stl.period_name))
                WHEN cp.payment_frequency = 'yearly' THEN
                    (SUM(so.amount_untaxed) / COUNT(DISTINCT stl.period_name))
                ELSE 0
            END AS distributed_sales_amount
        FROM
            sale_order so
            JOIN res_users ru ON so.user_id = ru.id
            JOIN commission_plan_salesperson cps ON cps.salesperson_id = ru.id
            JOIN commission_plan cp ON cps.commission_plan_id = cp.id
            LEFT JOIN salesperson_target_line stl ON stl.commission_plan_salesperson_id = cps.id
                AND so.date_order >= stl.start_date
                AND so.date_order <= stl.end_date
        WHERE
            so.state = 'sale' -- Only include confirmed sale orders
            AND so.date_order >= cp.effective_period_start
            AND so.date_order <= cp.effective_period_end
        GROUP BY
            cp.id, ru.id, stl.period_name, stl.target_amount, cp.payment_frequency
        )
        """)
