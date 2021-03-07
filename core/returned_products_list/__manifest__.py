# -*- coding: utf-8 -*-
{
    'name': 'Returned Products List',
    'version': '1.1.1',
    'category': 'Stock',
    'sequence': 17,
    'summary': 'setup to view a list of returned products.',
    'description': "This module includes setup to view a list of returned products.",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kannan',
    'depends': [
        'return_remarks'
    ],
    'data': [
        'wizard/stock_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}