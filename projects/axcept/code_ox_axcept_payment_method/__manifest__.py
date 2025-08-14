{
    'name': 'Axcept Payment Method',
    'summary': 'Axcept Payment Method sub-menu on Accountant Configuration',
    'description': 'Axcept Payment Method sub-menu',
    'website': 'https://code-ox.com/',
    'author': 'Code-Ox Technologies',
    'category': 'Accounting',
    'version': '1.0',
    'depends': [
        'contacts',
        'base',
        'accountant'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/axcepy_payment_method.xml',
        'views/account_journal.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}
