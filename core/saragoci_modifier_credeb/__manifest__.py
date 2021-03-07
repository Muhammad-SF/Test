# -*- coding: utf-8 -*-
{
    'name': "saragoci_modifier_credeb",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "HashMicro/ Sang",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Web',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'credit_debit_note'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    #Load qweb
    #'qweb': ['static/src/xml/*.xml'],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}