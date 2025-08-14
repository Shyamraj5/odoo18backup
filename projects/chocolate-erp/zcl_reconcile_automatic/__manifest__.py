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
        'security/ir.model.access.csv',
        'views/account_payment_views.xml',
    ],

}

