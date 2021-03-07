# -*- coding: utf-8 -*-
{
    'name': "stock_move_manufacturing",

    'summary': """
       Create stock move for manufacturing process""",

    'description': """
        Create stock move for manufacturing process
    """,

    'author': "HashMicro/Quy",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'mrp',
    'version': '1.2.2',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'mrp', 'manufacturing_order_extended', 'internal_transfer_manufacturing'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/mrp_production_view.xml',
        # 'views/mrp_bom_view.xml',
        'views/mrp_workorder_view.xml',

    ],
    # only loaded in demonstration mode

}