{
    'name': 'Dashboard',
    'version': '1.0',
    'summary': '',
    'description': 'Manage your tasks with this To-Do List module.',
    'author': 'shyamraj km',
    'depends': ['web','sale','board'],
    'data': [
        "views/dashboard.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'sym_sales_dashboard/static/src/components/**/*.js',
            'sym_sales_dashboard/static/src/components/**/*.xml',
    ],
    },
    'application': True,
}