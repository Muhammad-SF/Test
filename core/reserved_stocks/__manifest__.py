# -*- coding: utf-8 -*-
{
    'name': 'Reserved Stocks',
    'version': '1.1.1',
    'category': 'Stock',
    'sequence': 17,
    'summary': 'setup for user to view a list of reserved stocks and reserved by whom.',
    'description': "This module includes setup for user to view a list of reserved stocks and reserved by whom.",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kannan',
    'depends': [
        'sale_stock'
    ],
    'data': [
        'views/stock_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}