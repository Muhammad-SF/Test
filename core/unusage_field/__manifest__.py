# -*- coding: utf-8 -*-
{
    'name': "unusage field",

    'summary': """ hide unusage field""",

    'description': """
    """,

    'author': "HashMicro",
    'website': "http://www.hashmicro.com",

    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'products',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['product', 'stock'],

    # always loaded
    'data': [
        'views/product_view.xml',
    ],

    'auto_install': True,
    'installable': True,
    'application': False


}
