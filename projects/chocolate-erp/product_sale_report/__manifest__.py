{
    "name": "Sale Product Excel Report",
    "summary": """sales Excel Report.""",
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    "license": "LGPL-3",
    "category": "Sales",
    "version": "18.0.0.0",
    "depends": ['base', 'sale', 'sales_team', 'web', 'report_xlsx', 'account'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/product_sale_report_wizard.xml',
        'reports/product_sale_report.xml',

    ],
}