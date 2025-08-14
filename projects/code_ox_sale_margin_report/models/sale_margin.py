from odoo import models, fields, tools

class SaleOrderMarginView(models.Model):
    _name = 'sale.order.margin.view'
    _description = 'Sale Order Margin Analysis View'
    _auto = False
    _table = 'sale_order_margin_view'
    _rec_name = 'order_name'

    order_name = fields.Char(string='Order Reference', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)

    order_id = fields.Many2one('sale.order', string="Order")
    product_id = fields.Many2one('product.product', string="Product")
    product_uom_qty = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Unit Price")
    margin_percent = fields.Float(string="Margin (%)")
    order_date = fields.Date(string="Order Date", readonly=True)
    sales_person = fields.Many2one('res.users', string='Salesperson', readonly=True)
    margin = fields.Float(string='Margin Amount', readonly=True)
    cost = fields.Float(string="Cost",readonly=True)

    def _get_sql_view(self, extra_where=""):
        """
        Returns the main SQL for the view with optional extra WHERE.
        """
        return f"""
            CREATE OR REPLACE VIEW {self._table} AS (
            SELECT
                sol.id AS id,
                so.id AS order_id,
                so.name AS order_name,
                so.date_order AS order_date,
                so.partner_id AS partner_id,
                so.user_id AS sales_person,
                sol.product_id AS product_id,
                sol.product_uom_qty AS product_uom_qty,
                sol.price_unit AS price_unit,
                sol.margin_percent AS margin_percent,
                sol.margin AS margin,
                sol.purchase_price AS cost
            FROM sale_order_line sol
            JOIN sale_order so ON sol.order_id = so.id
            WHERE so.state IN ('sale', 'done')
            {extra_where}
        )
        """


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(self._get_sql_view())