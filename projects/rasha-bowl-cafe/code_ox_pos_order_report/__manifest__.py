{
    'name':'POS Order Report',
    'version':'18.0.1.0',
    'summary': 'POS Order Report',
    'license':'LGPL-3',
    'category':'Point of Sale',
    'author':'CODE-OX Technologies',
    'depends': [
        'web',
        'point_of_sale',
        'report_xlsx',
        'code_ox_pos_generic_customisation'
    ],
    'data':[
        'security/ir.model.access.csv',
        'reports/order_report_views.xml',
        'reports/order_report_template.xml',
        'wizard/order_report_wizard.xml',
        'views/report_templates.xml',
        
        ],

}