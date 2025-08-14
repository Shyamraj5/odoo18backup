{
    'name': 'Replenishment Notification',
    'version': '18.0.1.0',
    'summary': 'Replenishment Notification',
    'author': 'CODE-OX',
    'website': 'https://code-ox.com',
    'license': 'LGPL-3',

    'depends': ['stock','web_notify','mail'],

    'data': [
        'security/res_groups.xml',
        'data/check_replenishment.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
