{
    'name' : 'Purchase Generic',
    'version' : '18.0.1.0',
    'summary' : 'Purchase Generic',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': [
        'purchase', 
        'purchase_requisition',
        'wm_purchase_global_discount',
        'account',
    ],
    'data':[
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/purchase.xml',
        'views/res_partner.xml',
        'views/account_move.xml',
        'views/stock_picking.xml',
        ],
    'assets': {
        'web.assets_backend': [
            'purchase_generic/static/src/components/tax_totals/tax_totals.xml'
        ],
    },
}  
