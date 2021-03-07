# -*- coding: utf-8 -*-
{
    'name': "Sale Order Revisions",

    'summary': """
        Sale Order Revisions""",

    'description': """
        Sale Order Revisions
    """,

    'author': 'HashMicro / Vu',
    'website': 'http://www.hashmicro.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'HashMicro',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
    ],

    # always loaded
    'data': [
        'views/sale_order_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'post_init_hook': 'populate_unrevisioned_name',
}