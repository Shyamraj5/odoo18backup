{
    'name': 'Wallet',
    'version': '1.0',
    'category': 'Accounting',
    'summary': '',
    'description': "",
    'author': 'Code-Ox',
    'website': 'https://code-ox.com',
    'depends': ['base', 'account'],
    'data': [
        "security/ir.model.access.csv",
        "views/wallet.xml"
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}