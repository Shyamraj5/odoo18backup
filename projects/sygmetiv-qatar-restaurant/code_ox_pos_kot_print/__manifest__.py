{
    'name': 'POS KOT Generic Customizations',
    'version': '18.0.1.0',
    'summary': 'POS KOT Generic Customizations',
    'license': 'LGPL-3',
    'category': 'POS',
    'author': 'CODE-OX Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['base','web','point_of_sale'],
    'data': [
        'views/pos_config.xml',
    ],
    'assets':{
        'point_of_sale._assets_pos': [
            'code_ox_pos_kot_print/static/src/**/*',
        ],
    },
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}