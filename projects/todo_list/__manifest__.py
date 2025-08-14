{
    'name': 'To-Do List',
    'version': '1.0',
    'summary': 'A simple To-Do List application',
    'description': 'Manage your tasks with this To-Do List module.',
    'author': 'Your Name',
    'depends': ['web'],
    'data': [
        "security/ir.model.access.csv",
        "views/todo_action.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'todo_list/static/src/components/js/todo_list.js',
            'todo_list/static/src/components/xml/todo_list.xml',
            'todo_list/static/src/components/js/categories.js',
            'todo_list/static/src/components/xml/categories.xml'
        ],
    },
    'application': True,
}