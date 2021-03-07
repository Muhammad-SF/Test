# -*- coding: utf-8 -*-
{
    'name': 'Search By Date Range',
    'version': '1.1.1',
    'category': 'web',
    'summary': 'Search by date range in List view and Pivot view',
    'description': """

Search by date range in List view and Pivot view
--------------------------------------------------

    """,
    'author': 'Vijay Maurya',
    'depends': ['web'],
    'data': [
        'views/template_view.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    "price": 0.00,
    "currency": "EUR",
    
    'images': ['static/description/list_pivot.png'],

    'installable': True,
    'auto_install': True,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
