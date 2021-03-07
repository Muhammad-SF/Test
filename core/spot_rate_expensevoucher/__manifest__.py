# -*- coding: utf-8 -*-
{
    'name': "Spot Rate Expensevoucher",
    'author': 'HashMicro/Antsyz-Kannan',
    'version': '1.1.1',
    'sequence': 102,
    'summary': 'To multiply spot rate with voucher amount for journal entries.',
    'description': 'This modules include to muliplication of spot rate with voucher amount for journal entries.',
    'website': 'www.hashmicro.com',
    'category': 'account',
    'depends': ['sg_expensevoucher'],
    'data': [
        'views/account_voucher_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,

}