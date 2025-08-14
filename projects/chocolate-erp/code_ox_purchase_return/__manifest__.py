{
    "name": "Purchase Return",
    "summary": """Module for managing the returning of goods received from purchase order.""",
    "license": "LGPL-3",
    "category": "Purchase",
    "version": "18.0.0.0",
    "website": "https://code-ox.com/",
    "author": "Code-Ox Technologies",
    "depends": ["purchase", "stock"],
    "data": [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/purchase_return.xml',
        'wizard/purchase_return_round_off.xml'
    ],
}