# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

{
    'name': 'Stock Inventory Valuation Report On Particular Date',
    'version': '1.1.1',
    'category': 'stock',
    'summary': 'Past Date Stock With Valuation Report in XLS/PDF',
    'description': """
Stock Valuation Report on Date,
----------------------------------
""",
    'author': 'TidyWay',
    'website': 'http://www.tidyway.in',
    'depends': ['stock', 'report'],
    'data': [
        'security/stock_valuation_security.xml',
        'wizard/stock_valuation.xml',
        'views/stock_valuation_menu.xml',
        'views/stock_valuation_template.xml'
    ],
    'price': 199,
    'currency': 'EUR',
    'installable': True,
    'license': 'OPL-1',
    'application': True,
    'auto_install': False,
    'images': ['images/valuation.jpg'],
    'live_test_url' : 'https://youtu.be/T37XNAYv6I8'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
