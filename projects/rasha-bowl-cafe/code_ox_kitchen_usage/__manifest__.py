{
    'name': 'Kitchen Usage',
    'version': '1.0',
    'summary': 'A custom module with a new form view',
    'description': 'This module adds a new model and form view.',
    'author': 'Your Name',
    'depends': ['base','stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/kitchen_usage.xml',
        'views/kitchen_procurement_view.xml',
        'views/kitchen_setting.xml',
        
    ],
    # 'installable': True,
    # 'application': True,
}
