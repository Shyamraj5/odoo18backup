{
    'name': 'Product Offers',
    'version': '1.0',
    'category': 'Sales',
    'description': 'Module to manage product offers',
    'author': 'Code-ox Technologies',
    'depends': ['sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_offer.xml',
    ],
    'installable': True,
    'application': False,
}
