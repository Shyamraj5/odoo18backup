{
    'name': 'Self Order Customisation',
    'version': '18.0.1.0.0',
    'summary' : 'Self Order Customisation',
    'author': 'CODE-OX',
    'license': 'LGPL-3',
    'depends': ['base','product','stock','pos_self_order'],

    'data':[
        'views/product_template.xml',

    ],
    'assets':{
        'pos_self_order.assets': [
            'self_order_customisation/static/src/product_card/pos_product_card.xml',
        ],
    },

    'installable': True,
    'auto_install': False,
}
