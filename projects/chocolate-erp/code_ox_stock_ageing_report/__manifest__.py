{
    'name': 'Stock Ageing Report',
    'version': '18.0.1.0.0',
    'summary' : 'Stock Ageing Report',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com/',
    'license': 'LGPL-3',
    'depends': ['stock', 'report_xlsx'],

    'data':[
        'security/ir.model.access.csv',
        'report/report.xml',
        'wizard/stock_ageing_report_wizard.xml',
    ],

    'installable': True,
    'auto_install': False,
}