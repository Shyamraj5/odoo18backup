{
    'name': 'Cash Summary Report',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Reports',
    'summary': 'Generate PDF reports for account balances by company',
    'depends': [ 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cash_summary_report_wizard_view.xml',
        'report/cash_summary_report_template.xml',
        'report/cash_summary_report.xml',
    ],
    
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}