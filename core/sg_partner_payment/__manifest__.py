# -*- coding: utf-8 -*-
{
    'name': 'Sg Partner Payment',
    'author': 'HashMicro/Antsyz-Saravanakumar, Kannan & Mareeswaran',
    'version': '1.2.27',
    'summary': 'customer and supplier payment',
    'description': 'This module includes customer and supplier bulk payment functionality',
    'website': 'www.hashmicro.com',
    'category': 'account',
    'depends': ['credit_debit_note','account_cancel','account_cancel', 'approval_matrix_config','payment'],
    'data': [
        'security/ir.model.access.csv',
        'security/partner_payment_security.xml',
        'views/res_config_view.xml',
        'views/receipt_payment_approving_matrix_view.xml',
        'views/receipt_payment_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}