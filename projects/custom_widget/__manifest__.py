{
    "name": "Custom widget",
    "summary": """Module for Sale Activity.""",
    "author": "CODE-OX",
    "website": "https://www.code-ox.com/",
    "license": "LGPL-3",
    "category": "Accounting",
    "version": "18.0.0.0",
    "depends": ["sale","web"],
    'assets': {
        'web.assets_backend': [
            'custom_widget/static/src/js/**.js',
            'custom_widget/static/src/xml/**.xml',
        ],
    },
    "data":[
        "views/sale.xml",
    ],
    'installable': True,
    'application': True,
}
