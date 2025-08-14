{
    "name": "Sales Round-off Button",
    "summary": """Module to implement Sales Round-off Button""",
    "author": "Code-Ox",
    "license": "LGPL-3",
    "category": "Sales",
    "version": "18.0.0.1",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/product_data.xml",
        "views/sale_order.xml",
        "wizard/sale_round_off.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'code_ox_sales_round_off/static/src/xml/tax_totals.xml'
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',

}
