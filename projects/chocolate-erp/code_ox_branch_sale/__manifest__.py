{
    'name': 'Branch sale',
    'version': '18.0.1.0.0',
    'category': 'sale',
    "website": "https://code-ox.com/",
    "author": "Code-Ox Technologies",
    'depends': [ 'base','product','stock','sale', 'sales_generic_customisation'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/branch_transfer_out_sequence.xml',
        'data/branch_transfer_in_sequence.xml',
        'views/branch_transfer_out.xml',
        'views/branch_transfer_in.xml',
        'views/product_category_inherit.xml',
        'views/res_config_settings.xml',
        'views/stock_lot.xml',
        'views/res_company.xml',
    ],
    'images': [
        "static/description/icon.png",
    ],
    
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}