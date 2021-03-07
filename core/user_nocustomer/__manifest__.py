# -*- coding: utf-8 -*-
{
    'name': "user_nocustomer",

    'summary': """
        user_nocustomer""",

    'description': """
        user_nocustomer
    """,

    'author': "HashMicro / Sang",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],
    'auto_install': True,

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}