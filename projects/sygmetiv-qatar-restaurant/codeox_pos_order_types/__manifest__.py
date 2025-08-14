{
    'name': 'POS Order Types',
    'version': '18.0.1.0',
    'summary': 'POS Generic Customizations',
    'license': 'LGPL-3',
    'category': 'POS',
    'author': 'CODE-OX Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['base','web','point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order.xml',
        'views/pos_order_type.xml',
        'views/pos_config.xml',
    ],
    'assets':{
        'point_of_sale._assets_pos': [
            'codeox_pos_order_types/static/src/**/*',
        ],
    },
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}