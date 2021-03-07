# -*- coding: utf-8 -*-
{
    'name': 'Spot Rate Register Payment',
    'version': '1.1.1',
    'category': 'Accounting',
    'sequence': 0,
    'summary': 'Spot rate when register payment',
    'description': 'Adds a Spot Rate field in register payment screen and create a JE for the Spot Rate',
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Antsyz-Saravanakumar',
    'depends': ['account_accountant', 'sg_partner_payment'],
    'data': [
        'views/account_payment_view.xml',
    ],
    'installable': True,
    'application': True,
}