# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Product Sale Purchase History",
    "version": "18.0.1.1.1",
    "author": "CODE-OX",
    'website': 'https://code-ox.com/',
    "license": "LGPL-3",
    "depends": ['sale', 'purchase'],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_views.xml",
        "wizards/sale_purchase_history.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "product_transaction_history/static/src/js/*.js",
            "product_transaction_history/static/src/xml/*.xml",
        ],
    },
    "installable": True,
}
