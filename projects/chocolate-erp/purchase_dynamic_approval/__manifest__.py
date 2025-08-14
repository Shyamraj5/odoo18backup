{
    'name': 'Purchase Dynamic Approval',
    'version': '18.0.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Dynamic, Customizable and Flexible Approval Process for Purchase Orders',
    'license': "OPL-1",
    'author': 'CODE-OX',
    'website': 'https://code-ox.com/',
    'depends': ['base', 'purchase','purchase_generic'],
    
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_teams_views.xml',
        'views/purchase_order_view.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
