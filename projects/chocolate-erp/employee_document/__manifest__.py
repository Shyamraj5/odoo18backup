{
    'name': 'Employee Document Management',
    'version': '18.0.1.0.0',
    
    'depends': ['base', 'hr','code_ox_account_generic_customisation'],
    'data': [
        'security/ir.model.access.csv',
        'views/employee_views.xml',
        'data/email_template.xml',
        'data/expiry_corn.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}