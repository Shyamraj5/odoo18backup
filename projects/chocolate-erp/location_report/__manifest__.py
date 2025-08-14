{
    'name': 'Location Report',
    'version': '18.0.1.0.0',
    'summary' : 'Detailed Location Report',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com/',
    'license': 'LGPL-3',
    'depends': ['sale', 'base', 'report_xlsx', 'van_sale'],

    'data':[
        'security/ir.model.access.csv',
        'reports/location_report.xml',
        'wizard/location_report_wizard.xml',
    ],

    'installable': True,
    'auto_install': False,
}