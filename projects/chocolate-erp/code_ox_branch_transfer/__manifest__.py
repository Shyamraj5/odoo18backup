{
    'name': 'Branch Transfer',
    'version': '18.0.1.0.0',
    'category': 'sale',
    'summary': 'Branch Transfer',
    'description': """""",
    "website": "https://code-ox.com/",
    "author": "Code-Ox Technologies",
    'depends': ['sale', 'purchase', 'purchase_sale_inter_company'],
    'data': [
        'views/branch_transfer.xml',
        'views/account_move.xml',
        'views/res_config_settings.xml',
        'data/margin_product.xml',
    ],
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}