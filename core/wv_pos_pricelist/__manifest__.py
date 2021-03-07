# -*- coding: utf-8 -*-

{
    'name': 'Pos Pricelist',
    'version': '1.1.1',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'Pos price list allows you to add price list in point of sale.',
    'description': """

=======================

Pos price list allows you to add price list in point of sale.

""",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml'
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/pos_list.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 39,
    'currency': 'EUR',
}
