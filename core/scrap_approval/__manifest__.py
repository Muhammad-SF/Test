# -*- coding: utf-8 -*-
{
    'name': "Scrap Approval",

    'summary': """
        Create a new function to setup scrap approval process and functions.""",

    'description': """
        Create a new function to setup scrap approval process and functions.
    """,

    'author': "HashMicro/ Krupesh",
    'website': "https://www.hashmicro.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Inventory',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'wizard/scrap_reason_view.xml',
        'wizard/scrap_return_view.xml',
        'views/stock_scrap_view.xml',
        # 'views/views.xml',
        # 'views/templates.xml',
        #'data/scrap_approval_seq.xml',
        #'views/scrap_approval_view.xml',
        'views/scrap_matrix_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
