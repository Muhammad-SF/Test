# -*- coding: utf-8 -*-
{
    'name': "Sale Sourced by Line",

    'summary': """
Adds the possibility to source a line of sale order from a specific
warehouse instead of using the warehouse of the sale order.""",

    'description': """
Sale Sourced by Line
====================

Adds the possibility to source a line of sale order from a specific
warehouse instead of using the warehouse of the sale order.

This will create one procurement group per warehouse set in sale
order lines.

It will only supports routes such as MTO and Drop Shipping.

Contributors
------------

* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
    """,

    'author': "HashMicro / Vu",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'HashMicro',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale_stock',
        'sale_procurement_group_by_line',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'test': [
        'test/sale_order_source.yml',
        'test/sale_order_multi_source.yml',
        'test/sale_order_not_sourced.yml',
    ],
    'auto_install': False,
    'installable': True,
}