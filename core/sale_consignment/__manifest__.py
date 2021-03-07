# -*- coding: utf-8 -*-
{
    'name': "Sales Consignment",

    'summary': """
        Sales Consignment""",

    'description': """
        Sales Consignment custom Module
    """,

    'author': "HashMicro / Rupam / Vu",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sale',
        'sale_stock',
        'account_voucher',
        # 'purchase',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/models_views.xml',
        'views/custom_css_views.xml',
        'data/commission_sequence.xml',
        'report/commission_report_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
