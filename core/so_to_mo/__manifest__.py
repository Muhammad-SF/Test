# -*- coding: utf-8 -*-
{
    'name': "so_to_mo",

    'summary': """
       Create Manufacturing Plan from Sales order""",

    'description': """
        Create Manufacturing Plan from Sales order
    """,

    'author': "HashMicro / Dev (Braincrew Apps)",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'mrp',
    'version': '1.2.4',

    # any module necessary for this one to work correctly
    'depends': ['mrp', 'sale', 'stock', 'manufacturing_plan','mrp' ],#'description_so_po',

    # always loaded
    'data': [
        'views/product_view.xml',
    ],

}
