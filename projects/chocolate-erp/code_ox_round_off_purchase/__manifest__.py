{
    'name' : 'Round Off Wizard',
    'version' : '18.0.1.0',
    'summary' : 'Purchase Round Off',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': [
        'purchase','wm_purchase_global_discount','code_ox_sales_round_off',
    ],
    'data':[
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
        'wizard/purchase_round_off_wizard.xml',
        ],
}  
