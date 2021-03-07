# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product Exchange',
    'version': '1.1.1',
    'category': 'Purchases',
    'author': 'HashMicro/Shivam',
    'depends': ['purchase', 'sales_purchase_return_status', 'vendor_quantitative_kpi'],
    'description': """
                  Product Exchange
    """,
    'data': [
        'data/ir_sequence_data.xml',
        'views/manual_return_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
