{
    "name": "Sale Fixed Discount",
    "summary": "Allows to apply fixed amount discounts in sale.",
    "version": "18.0.1.0.0",
    "category": "Sale",
    "author": "Code-Ox Technologies LLP",
    "company": "Code-Ox Technologies LLP",
    "maintainer": "Code-Ox Technologies LLP",
    "website": "https://code-ox.com/",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["sale", "code_ox_account_invoice_fixed_discount"],
    "data": [
        "views/sale_order.xml",
        "wizard/sale_order_discount.xml",
    ],
    'images': [
        "static/description/icon.png",
    ],
}
