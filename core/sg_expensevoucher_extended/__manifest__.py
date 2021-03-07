# -*- coding: utf-8 -*-
{
    'name': 'SG Expense Voucher Extended',
    'version': '1.1.1',
    'category': 'Accounting',
    'sequence': 19,
    'summary': 'Extend Functionality of journal entry in voucher',
    'description': "This module Extend Functionality of journal entry in voucher",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Mak-Wizard Technolab',
    'depends': ['sg_expensevoucher'],
    'data': [
        'views/account_voucher_view.xml',
    ],
    'installable': True,
    'application': True,
}