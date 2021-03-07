# -*- coding: utf-8 -*-
{
    'name': "Sale Procurement Group by Line",

    'summary': """
        Base module for multiple procurement group by Sale order""",

    'description': """
        Base module for multiple procurement group by Sale order
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
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'auto_install': False,
    'installable': True,
}