# -*- coding: utf-8 -*-
{
    'name': 'Untaken Stock',
    'version': '1.2.1',
    'category': 'Inventory',
    'summary': '',
    'description': "This module Filter Project and Event base on login user",
    'website': 'www.hashmicro.com',
    'author': 'Hashmicro/GYB IT SOLUTIONS-Trivedi',
    'depends': [
        'full_inv_adjustment','stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/untaken_stock.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': True,
}
