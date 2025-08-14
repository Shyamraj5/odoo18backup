{
    'name': 'POS Customizations',
    'version': '18.0.1.0',
    'summary': 'POS Customizations',
    'license': 'LGPL-3',
    'category': 'POS',
    'author': 'CODE-OX Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['base','web','pos_self_order'],
    'assets':{
        'web.assets_backend': [
            'pos_generic_customizations/static/src/xml/cart_page.xml',
            'pos_generic_customizations/static/src/xml/order_widget.xml',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}
