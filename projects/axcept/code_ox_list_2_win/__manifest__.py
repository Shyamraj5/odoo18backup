{
    'name': 'List2Win Integration',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Integration module for List2Win',
    'description': """
        List2Win Integration Module
        ==========================
        * Integrate List2Win functionality
        * Manage List2Win synchronization
    """,
    'author': 'Code-Ox',
    'website': 'https://code-ox.com',
    'depends': ['base', 'account', 
                'code_ox_be_partner_customisation', 'code_ox_be_partner_customisation',
                'code_ox_partner_generic_customisation', 'stock'
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/service_product.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}