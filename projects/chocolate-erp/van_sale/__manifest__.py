{
    'name': 'Sales Person Management',
    'version': '18.0.1.0.0',
    'summary': 'Manage Sales Persons and their Journeys',
    'description': """
        Module to manage sales persons, track their journeys, and record start and end kilometers.
    """,
    'category': 'Sales',
    'author': 'code-ox technologies',
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/trip.xml',
        'views/res_partner.xml',
        'views/sales_person_route.xml',
        'views/route_assign.xml',
        'views/van_master.xml',
        'views/van_allocation.xml',
        'views/menu.xml'
    ],
    'depends': ['base', 'web','sale','stock','sales_team'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
