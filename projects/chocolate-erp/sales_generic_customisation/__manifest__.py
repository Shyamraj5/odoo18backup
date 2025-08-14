{
    'name' : 'Sales Generic Customisation',
    'version' : '18.0.1.0',
    'summary' : 'Additional field to separate wholesale,b2b and vansale',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': ['sale', 'stock', 'account', 'sales_team', 
                'sale_order_lot_selection','code_ox_account_generic_customisation',
                'code_ox_sales_round_off', 'sale_margin', 'product_offer', 'generic_inventory'],
    'data':[    
            'security/ir.model.access.csv',
            'views/res_config_settings.xml',
            'views/sale_order_view.xml',
            'views/promotional_sale.xml',
            'views/account_move.xml',
            'wizard/sale_order_discount.xml',
    ],
}