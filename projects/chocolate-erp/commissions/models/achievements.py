from odoo import models, fields, api
from odoo import tools

class Achievement(models.Model):
    _name = 'commission.achievements'
    _description = 'Achievements'
    _auto = False
    _table = 'achievement_sql_view'

    commission_plan = fields.Char("Commission Plan")
    sales_person = fields.Many2one("res.users", "Sales Person")
    achieved = fields.Float("Achieved")
    date = fields.Date("Date", column_name='order_date')
    period = fields.Char("Period")
    source = fields.Many2one("sale.order", "Source")

    def action_view_source(self):
        """
        Action to open the related sale order form view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.source.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        CREATE OR REPLACE VIEW achievement_sql_view AS (
        SELECT
            ROW_NUMBER() OVER () AS id, -- Generate unique IDs for the view
            cp.name AS commission_plan,
            ru.id AS sales_person,
            SUM(sol.price_subtotal) AS achieved, -- Sum of untaxed amount
            so.date_order AS date,
            CONCAT(EXTRACT(YEAR FROM cp.effective_period_start), ' Q', EXTRACT(QUARTER FROM cp.effective_period_start)) AS period,
            so.id AS source
        FROM sale_order so
        JOIN sale_order_line sol ON sol.order_id = so.id
        JOIN res_users ru ON so.user_id = ru.id
        JOIN commission_plan_salesperson cps ON cps.salesperson_id = ru.id
        JOIN commission_plan cp ON cps.commission_plan_id = cp.id
        WHERE so.date_order >= cp.effective_period_start
        AND so.date_order <= cp.effective_period_end
        AND so.state = 'sale' -- Only include confirmed sale orders
        GROUP BY cp.name, ru.id, so.date_order, so.id, cp.effective_period_start
        )
        """)

