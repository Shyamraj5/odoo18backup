{
    'name' : 'Commission Plan',
    'version' : '18.0.1.0',
    'summary' : 'Manage Commission Plans in Sales',
    "author": "CODE-OX",
    "website": "https://code-ox.com/",
    'license' : 'LGPL-3',
    'depends': ['sale','sales_team'],
    'data':[
          'security/ir.model.access.csv',   
          'views/commission_views.xml',
          'views/incentive_views.xml',
          'views/achievements_views.xml',
          'views/commission_menu.xml',
    ],
}