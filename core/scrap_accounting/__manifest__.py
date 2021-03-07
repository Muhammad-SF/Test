# -*- coding: utf-8 -*-
{
    'name': "scrap_accounting",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "HashMicro/Vu",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'stock_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/product.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}