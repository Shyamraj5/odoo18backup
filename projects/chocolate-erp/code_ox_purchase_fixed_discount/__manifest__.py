{
    "name": "Purchase Fixed Discount",
    "summary": "Allows to apply fixed amount discounts in purchase.",
    "version": "18.0.1.0.0",
    "category": "Purchase",
    "author": "Code-Ox Technologies LLP",
    "company": "Code-Ox Technologies LLP",
    "maintainer": "Code-Ox Technologies LLP",
    "website": "https://code-ox.com/",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["purchase", "code_ox_account_invoice_fixed_discount", "wm_purchase_global_discount"],
    "data": [
        "views/purchase_order.xml",
        "wizard/purchase_order_discount.xml",
    ],
    'images': [
        "static/description/icon.png",
    ],
}
