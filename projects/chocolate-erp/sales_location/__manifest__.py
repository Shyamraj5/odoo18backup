{
    'name': 'Sales Location',
    'version': '18.0.1.0.0',
    'summary' : 'Select Sales Location',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com/',
    'license': 'LGPL-3',
    'depends': ['sale', 'sales_generic_customisation', 'sale_order_lot_selection'],

    'data':[
        'views/sale_order.xml',
    ],

    'installable': True,
    'auto_install': False,
}