# -*- coding: utf-8 -*-
{
    'name': 'Sales Bank Charges',
    'version': '1.1.1',
    'category': 'Account/ Bank Charges',
    'sequence': 15,
    'summary': 'Deducting Bank Charges from Invoice payment',
    'description': "Deducting Bank Charges",
    'website': 'http://www.axcensa.com/',
    'author': 'Hashmicro/Axcensa',
    'depends': ['base', 'account'],
    'data': [
        'views/sales_bankcharges_view.xml'
    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}