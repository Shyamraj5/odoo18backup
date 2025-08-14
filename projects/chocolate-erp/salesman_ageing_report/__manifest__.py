{
    'name': 'Salesman Ageing Report',
    'version': '18.0.1.0.0',
    'summary' : 'Detailed Salesman Ageing Report',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com/',
    'license': 'LGPL-3',
    'depends': ['sale', 'base', 'report_xlsx'],

    'data':[
        'security/ir.model.access.csv',
        'reports/salesman_ageing_report.xml',
        'wizard/ageing_report_wizard.xml',
    ],

    'installable': True,
    'auto_install': False,
}