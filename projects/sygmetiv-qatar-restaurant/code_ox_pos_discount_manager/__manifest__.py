{
    'name': "POS Discount Manager Approval",
    'version': '18.0.1.0.1',
    'category': 'Point Of Sale',
    'summary': "Discount limit for each employee in every  point of sale",
    'description': """This module helps you to set a discount limit for each 
    employee in every  point of sale.It facilitate the manager  approval when 
    discount over the limit of employee""",
    'category': 'POS',
    'author': 'CODE-OX Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['pos_discount', 'hr','base','web'],
    'data': [
        'views/hr_employee_views.xml',
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'code_ox_pos_discount_manager/static/src/js/pos_store.js',
            'code_ox_pos_discount_manager/static/src/js/payment_screen.js',
            'code_ox_pos_discount_manager/static/src/js/control_button.js',
            ]
    },
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}