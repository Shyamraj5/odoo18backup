{
    "name": "PDC",
    "summary": """
        PDC""",
    "description": """
        Long description of module's purpose
    """,
    "author": "Code-Ox Technologies LLP",
    "website": "https://code-ox.com/",
    "category": "Accounting",
    "version": "18.0.2.3",
    "license": "LGPL-3",
    "depends": ['mail','code_ox_payment_approval_customisation'],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/sequence.xml",
        "data/cron.xml",
        "data/notification_activity.xml",
        "views/post_dated_check.xml",
        "views/account_account.xml",
        "views/res_company.xml",
        "views/pdc_server_action.xml",
        "wizards/bi_pdc_wizard_view.xml",
        "reports/paperformat.xml",
        "reports/payment_action.xml",
        "reports/payment_voucher_pdf_report.xml",
    ],
    "images": [
        "static/description/icon.png",
    ],
}
