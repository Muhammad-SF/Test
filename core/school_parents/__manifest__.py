# -*- coding: utf-8 -*-
{
    'name': "school_parents",

    'summary': """
       """,

    'description': """
       Parents profile
    """,

    'author': "HashMicro / Hoang",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'school'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/school_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}