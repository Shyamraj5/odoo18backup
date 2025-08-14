{
    'name': "POS Arabic Receipt",
    'version': '18.0.1.0.1',
    'category': 'Point Of Sale',
    'summary': "Arabic Receipt Printing for POS",
    'description': """This module helps you to print receipts in Arabic for each 
    transaction in the point of sale. It enhances the customer experience by providing 
    receipts in their preferred language.""",
    'category': 'POS',
    'author': 'CODE-OX Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['point_of_sale'],
    'data': [
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'code_ox_pos_arabic_receipt/static/src/**/*',
        ],
    },
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}

