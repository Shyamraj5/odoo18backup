from odoo import models, fields, tools
from odoo.exceptions import UserError

class MarginAnalysisWizard(models.TransientModel):
    _name = 'margin.analysis.wizard'
    _description = 'Margin Analysis Wizard'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    margin_percentage = fields.Float(string='Margin Percentage', required=True)
    comparison_operator = fields.Selection([
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('equals', 'Equals')
    ], string='Comparison', required=True, default='greater_than')

    def action_confirm(self):
        if not self.product_id or self.margin_percentage is False:
            raise UserError("Please fill all required fields")

        op_map = {
            'greater_than': '>',
            'less_than': '<',
            'equals': '='
        }
        operator = op_map.get(self.comparison_operator, '>')

        extra_where = f"""
            AND sol.product_id = {self.product_id.id}
            AND sol.margin_percent {operator} {self.margin_percentage}
        """

        tools.drop_view_if_exists(self.env.cr, 'sale_order_margin_view')
        self.env.cr.execute(
            self.env['sale.order.margin.view']._get_sql_view(extra_where)
        )

        return {
            'name': f'Margin Analysis for {self.product_id.display_name}',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.margin.view',
            'view_mode': 'list',
            'target': 'current',
        }
