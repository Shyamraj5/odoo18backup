{
    'name' : 'Scrap Loss Report',
    'version' : '18.0.1.0',
    'summary' : 'Detailed report of Scrap Loss Stock',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': ['base', 'stock', 'report_xlsx'],
    'data':[
              'security/ir.model.access.csv',
              'reports/scrap_loss_report.xml',
              'wizard/scrap_loss_wizard_view.xml',
    ],
}