# -*- coding: utf-8 -*-
{
    'name': 'Sales Analysis Based Currency',
    'version': '1.1.1',
    'category': 'sale',
    'summary': '',
    'description': "This module create new sales analysis report with convert amount base currency ",
    'website': 'www.hashmicro.com',
    'author': 'Hashmicro/Ankur',
    'depends': [
        'user_rate_po','sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/sale_report_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
}
