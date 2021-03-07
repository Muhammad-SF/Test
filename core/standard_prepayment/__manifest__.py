{
    'name' : 'Access to Account Recurring Entries',
    'version' : '2.1.4',
    'summary': 'Access To Recurring Entries',
    'sequence': 30,
    'description': """
    """,
    'category': 'Accounting',
    'website': 'https://www.hashmicro.com',
    'depends' : ['customer_prepayment', 'vendor_prepayment', 'recurring_invoice'],
    'data': [
        'security/prepayment_security.xml',
        'security/access_view.xml',
        'report/standard_prepayment_report_template.xml',
        'report/standard_prepayment_report.xml',
        'view/res_config_view.xml',
        'view/account_recurring_view.xml',
        'wizard/account_subscription_generate_view.xml',
            ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
