# -*- coding: utf-8 -*-
{
    'name': "vendor_payment_std",

    'summary': """
        vendor_payment_std
    """,

    'description': """
        vendor_payment_std
    """,

    'author': "HashMicro / Sang",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Web',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sg_partner_payment',
        'web_widget_many2many_tags_multi_selection',
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
}