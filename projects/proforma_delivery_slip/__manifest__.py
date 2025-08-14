{
    'name': 'Proforma Delivery Print',
    'version': '18.0.1.0.0',
    "category": "Accounting & Finance",
    "author": "Code-Ox Technologies LLP",
    "company": "Code-Ox Technologies LLP",
    "maintainer": "Code-Ox Technologies LLP",
    "website": "https://www.code-ox.com/",
    "license": "LGPL-3",
    'description': '''
        This module adds a Proforma Delivery print report that can be generated
        from Sales Orders, similar to the Proforma Invoice but focused on delivery details.
    ''',
    'depends': ['sale', 'stock'],
    'data': [
        'reports/proforma_delivery_report.xml',
        'reports/proforma_delivery_template.xml',
    ],
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}