{
    'name': 'Sale Order Margin Analysis',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Analyze sale order margins with filtering wizard',
    'description': """
        This module provides a margin analysis tool for sale orders with:
        - Wizard to filter by product and margin criteria
        - SQL view showing detailed margin calculations
        - Easy access through dedicated menu
    """,
    'author': 'Your Company',
    'depends': ['base', 'sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/margin_analysis_wizard_views.xml',
        'views/sale_order_margin_view_views.xml',
        'views/menu_items.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}