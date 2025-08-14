{
    'name': "POS Session Close Control",

    'summary': """ Point of Sale Session Close Control""",
    'description': """ Point of Sale Session Close Control""",

    'category': 'Sales/Point of Sale',
    'author': 'Adevx',
    'license': "OPL-1",
    'website': 'https://adevx.com',
    "price": 0,
    "currency": 'USD',

    'depends': ['point_of_sale'],
    'data': [
        # Views
        'views/pos_config.xml',
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "adevx_pos_close_session_control/static/src/**/*"
        ]
    },

    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
