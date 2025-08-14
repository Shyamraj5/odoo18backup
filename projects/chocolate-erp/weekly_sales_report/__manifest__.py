{
    'name' : 'Weelky Sales Report',
    'version' : '18.0.1.0',
    'summary' : 'Detailed report of weekly sales',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': ['sale', 'base', 'sales_generic_customisation', 'report_xlsx'],
    'data':[
              'security/ir.model.access.csv',
              'reports/weekly_sales_report.xml',
              'wizard/weekly_sales_wizard_view.xml',
    ],
}