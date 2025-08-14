{
    'name': 'code_ox_payroll_customisation',
    'version': '18.0.1.0.0',
    'category': 'HR Payroll',
    'summary': 'HR Payroll Customisation',
    'description': """""",
    "website": "https://code-ox.com/",
    "author": "Code-Ox Technologies",
    'depends': ['om_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'data/ir_sequence.xml',
        'views/other_allowance.xml',
        'views/hr_contract.xml',
    ],
    'images': [
        "static/description/icon.png",
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}