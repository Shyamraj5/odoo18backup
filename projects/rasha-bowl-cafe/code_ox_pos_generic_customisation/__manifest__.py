{
    'name': 'POS Generic Customizations',
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
        'views/product_template_inherit.xml',
        'views/product_product_inherit.xml',
    ],
    'assets':{
        'point_of_sale._assets_pos': [
            'code_ox_pos_generic_customisation/static/src/**/*',
        ],
        'web.assets_backend': [
        'code_ox_pos_generic_customisation/static/src/css/kanban_ribbon.css',
        ],
    },
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}