# -*- coding: utf-8 -*-
{
    'name': 'Sg Prepayment',
    'version': '1.1.1',
    'category': 'Accounting',
    'sequence': 18,
    'summary': 'setup for prepayment process',
    'description': "This module includes setup for prepayment process for both customer and supplier payments",
    'website': 'http://www.axcensa.com/',
    'author': 'Axcensa',
    'depends': [
        'account_accountant','l10n_sg'
    ],
    'data': [
        'data/account_data.xml',
        'data/account_invoice.xml',
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_use_model_view.xml',
        'wizard/prepayment_schedule.xml',
        'wizard/prepayment_schedule_cancel.xml',
        'wizard/prepayment_schedule_convert_revenue.xml',
        'views/account_view.xml',
        'views/customer_prepayment_schedule_view.xml',
        'views/supplier_prepayment_schedule_view.xml',
    'wizard/account_subscription_generate_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}