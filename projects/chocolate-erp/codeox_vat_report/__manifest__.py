{
    'name': 'VAT Report',
    'version': '18.0.1.0',
    'category': 'Accounting',
    'summary': 'VAT Report',
    'description': 'VAT report with both HTML and Qweb templates.',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com',
    'depends': ['base', 'account','account_dynamic_reports'],

    'data': [
            'security/ir.model.access.csv', 
            'view/menu.xml',
            'wizard/vat_report_wizard.xml',      
            'report/report.xml',
            'report/report_template.xml',
        ],
        
    'assets':{
        'web.assets_backend': [
            'codeox_vat_report/static/src/components/*.js',
            'codeox_vat_report/static/src/components/*.xml',
        ],
    },
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
