# -*- coding: utf-8 -*-
{
    'name': "Payable and Receivable Amount",

    'summary': "Manage Payable and Receivable Amounts in Odoo",

    'description': """This module helps in tracking payable and receivable amounts for customers and vendors.

    """,

    'author': "Zinfog Codelabs Pvt Ltd",
    'website': "<https://www.zinfog.com>",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],
    # 'depends': ['base','account','zcl_inventory','web','l10n_sa', 'om_account_accountant'],

    # always loaded
    'data': [
        'views/account_payment_views.xml',
    ],

}

