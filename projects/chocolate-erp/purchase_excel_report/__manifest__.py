{
    'name': 'Purchase Report',
    'version': '18.0.1.0.0',
    'summary' : 'Detailed Purchase Excel Report',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com/',
    'license': 'LGPL-3',
    'depends': ['purchase', 'base', 'report_xlsx'],

    'data':[
        'security/ir.model.access.csv',
        'reports/purchase_report.xml',
        'wizard/purchase_report_wizard.xml',
    ],

    'installable': True,
    'auto_install': False,
}
