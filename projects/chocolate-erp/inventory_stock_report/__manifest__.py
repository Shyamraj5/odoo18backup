{
    'name' : 'Inventory Stock Report',
    'version' : '18.0.1.0',
    'summary' : 'Detailed report of stocks in inventory',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': ['sale', 'base', 'stock', 'product', 'report_xlsx'],
    'data':[
              'security/ir.model.access.csv',
              'reports/inventory_stock_report.xml',
              'reports/stock_expiry_report.xml',
              'reports/stock_in_out_report.xml',
              'wizard/inventory_stock_wizard_view.xml',
              'wizard/stock_expiry_report_wizard.xml',
              'wizard/stock_in_out_wizard.xml'
    ],
}