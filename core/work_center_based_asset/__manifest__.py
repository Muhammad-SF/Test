# -*- coding: utf-8 -*-
{
    'name': "Work Center Based Asset",

    'summary': """
    Work Center Based Asset
       """,

    'description': """
        work center name a dropdown list of asset master
    """,

    'author': "hashmicro/Balram",
    'website': "www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'asset_maintenance_fleet_link'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}