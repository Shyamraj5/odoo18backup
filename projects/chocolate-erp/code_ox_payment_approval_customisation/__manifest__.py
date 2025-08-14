{
    "name": "code_ox_payment_approval_customisation",
    "version": "18.0.3.0.5",
    "summary": """ Account Payment Approval Customisation""",
    "description": """Account Payment Approval Customisation""",
    "author": "Code-Ox Technologies LLP",
    "company": "Code-Ox Technologies LLP",
    "maintainer": "Code-Ox Technologies LLP",
    "website": "https://code-ox.com/",
    "category": "Accounting",
    "depends": ["account", "codeox_multi_invoice_payment"],
    "data": [
        ""
        'security/ir.model.access.csv',
        "views/res_config_settings_views.xml",
        "views/payment_team.xml",
        "views/account_move.xml",
        "views/code_ox_account_payment.xml",
        "data/payment_approval.xml",
        "data/action.xml",
        "views/account_payment_register.xml",
    ],
    "images": [
        "static/description/icon.png",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}