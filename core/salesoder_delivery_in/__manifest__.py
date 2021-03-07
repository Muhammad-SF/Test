# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Salesoder Delivery In',
    'version': '1.1.1',
    'category': '',
    'sequence': 75,
    'summary': '',
    'author': 'Hashmicro / MpTechnolabs - Dipali',
    'description': """
    	Open the Incoming shipment insted of Delivery Order from Sale Order.
    """,
    'website': '',
    'images': [
    ],
    'depends': [
    	'sale', 'stock', 'sale_stock',
    ],
    'data': [
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [],
}
