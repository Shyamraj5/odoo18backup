{
    "name": "Sale Excel Report",
    "summary": """sales Excel Report.""",
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    "license": "LGPL-3",
    "category": "Sales",
    "version": "18.0.1.0.0",
    "depends": ['base', 'sale', 'sales_team', 'web', 'report_xlsx', 'stock'],
    "data": [
        'security/ir.model.access.csv',
        'reports/sales_report.xml',
        'reports/sales_target_report.xml',
        'reports/offer_sale_report.xml',
        'wizard/sales_excel_wizard_view.xml',
        'wizard/sales_target_wizard_view.xml',
        'wizard/offer_sales_wizard.xml',

    ],
}
