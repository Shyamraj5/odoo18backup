{
    'name' : 'Summary Sales Report',
    'version' : '18.0.1.0',
    'summary' : 'Summary report of sales',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': ['sale', 'base', 'sales_generic_customisation', 'report_xlsx'],
    'data':[
              'security/ir.model.access.csv',
              'reports/summary_sales_report.xml',
              'wizard/summary_sales_wizard_views.xml',
    ],
}