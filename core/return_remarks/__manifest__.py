# -*- coding: utf-8 -*-
{
    'name': 'Return Remarks',
    'version': '1.1.1',
    'category': 'Stock',
    'sequence': 17,
    'summary': 'setup to add the Return Reason and Remarks in Reverse Transfer wizard.',
    'description': "This module includes setup to add the Return Reason and Remarks in Reverse Transfer wizard.",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kannan',
    'depends': [
        'sale_stock'
    ],
    'data': [
        'views/return_reason_view.xml',
        'wizard/stock_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}