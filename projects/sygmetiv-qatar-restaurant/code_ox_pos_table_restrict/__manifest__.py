{
    'name': 'POS Table Restriction',
    'version': '18.0.1.0',
    'summary': 'POS Table Restriction',
    'license': 'LGPL-3',
    'category': 'POS',
    'author': 'CODE-OX Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['base','web','point_of_sale', 'pos_restaurant'],
    'data': [],
    'assets':{
        'point_of_sale._assets_pos': [
            'code_ox_pos_table_restrict/static/src/**/*',
        ],
    },
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}