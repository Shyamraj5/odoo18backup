{
    'name': 'POS Self Order Customizations',
    'version': '18.0.1.0',
    'summary': 'POS Self Order Customizations',
    'license': 'LGPL-3',
    'category': 'POS',
    'author': 'CODE-OX Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['base','web','pos_self_order'],
    'assets':{
        'pos_self_order.assets': [
            'code_ox_pos_self_order/static/src/**/*',
        ],
    },
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}