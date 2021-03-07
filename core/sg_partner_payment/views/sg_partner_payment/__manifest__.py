# -*- coding: utf-8 -*-
{
    'name': 'Sg Partner Payment',
    'author': 'HashMicro/Saravanakumar',
    'version': '1.1.1',
    'summary': 'customer and supplier payment',
    'description': 'This module includes customer and supplier bulk payment functionality',
    'website': 'www.hashmicro.com',
    'category': 'account',
    'depends': ['account_accountant'],
    'data': [
        'views/receipt_payment_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}