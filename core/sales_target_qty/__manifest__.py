# -*- coding: utf-8 -*-
{
    'name': "Sales Qty Target",

    'summary': """
        Add Sales Qty Target for Sales Team""",

    'description': """
        Add Sales Qty Target for Sales Team
    """,

    'author': "HashMicro/ Balaji(Antsyz) / Uday",
    'website': "http://www.hasmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm','hm_sales_standardization'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/salesperson_detail_view.xml',
        'report/sales_team_report.xml',
        'views/sales_team_views.xml',
        'views/sales_target_template.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    # only loaded in demonstration mode
    'demo': [
    ],
}