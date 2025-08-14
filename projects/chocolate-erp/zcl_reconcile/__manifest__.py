# -*- coding: utf-8 -*-
{
    'name': "Reconciliation",

    'summary': "Manage Reconciliation in Odoo",

    'description': """This module helps to do Reconciliation.

    """,

    'author': "Zinfog Codelabs Pvt Ltd",
    'website': "<https://www.zinfog.com>",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'views/account_payment_views.xml',
        'views/account_payment_reconcile_view.xml',
        'views/account_move_inherit.xml',
    ],

}

