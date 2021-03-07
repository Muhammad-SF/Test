# -*- coding: utf-8 -*-
{
    'name': "Simple Cash Advance",

    'summary': """
        Add manu cash advance""",

    'description': """
        Add manu cash advance
    """,

    'author': "Wangoes Technology/Pooja",
    'website': "http://www.wangoes.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['sg_hr_employee', 'hr', 'hr_expense'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}