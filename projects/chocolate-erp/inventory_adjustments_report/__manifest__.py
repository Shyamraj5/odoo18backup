{
    'name': 'Inventory Adjustments Report',
    'version': '18.0.1.0',
    'category': 'Inventory',
    'summary': 'Inventory Adjustments Report',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com',
    'depends': ['base', 'stock', 'report_xlsx'],

    'data': [
        'security/ir.model.access.csv',
        'reports/inventory_report.xml',
        'wizard/inventory_report_wizard.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
