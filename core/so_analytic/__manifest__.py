# -*- coding: utf-8 -*-
{
    'name': "so_analytic",

    'summary': """
        SO Analytic""",

    'description': """
        Allow setting of analytic accounts in SO, like Odoo 8, where you can select the analytic accounts per order line, and it will update invoice lines as well.
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
        'analytic',
        'sale',
    ],

    # always loaded
    'data': [
        'security/sale_security.xml',
        'views/account_config_settings.xml',
        'views/sale_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}