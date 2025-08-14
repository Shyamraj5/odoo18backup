# -*- coding: utf-8 -*-
{
    'name' : 'HR Employee Commitments',
    'version' : '18.0.1.0.0',
    'summary': "HR Employee Commitments",
    'description': """
                    Manages the commitments between HR and employee
                    """,
    'category': 'HR',
    'author': 'Code-Ox Technologies',
    'maintainer': 'Code-Ox Technologies',
    'website': 'https://code-ox.com/',
    'depends': ['hr'],
    'data':[
        'security/ir.model.access.csv',
        'views/hr_commitment.xml',
        'data/commitment_cron.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
