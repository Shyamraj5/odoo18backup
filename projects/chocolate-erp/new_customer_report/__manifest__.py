{
    'name' : 'New Customer Report',
    'version' : '18.0.1.0',
    'summary' : 'Detailed report of New Customers',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': ['sale', 'base', 'report_xlsx'],
    'data':[
              'security/ir.model.access.csv',
              'reports/new_customer_report.xml',
              "wizard/new_customer_wizard_view.xml"
    ],
}