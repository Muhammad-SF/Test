# -*- coding: utf-8 -*-
{
    'name': "simple_stock2",

    'summary': """
        Simple Stock Barcode""",

    'description': """
        Simple Stock Barcode
    """,

    'author': "HashMicro / Viet",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Warehouse',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'barcodes',
        'stock',
    ],

    # always loaded
    'data': [
        'data/simple_stock.xml',
        'security/ir.model.access.csv',
        'views/simple_stock_in_views.xml',
        'views/simple_stock_out_views.xml',
        'views/simple_stock_inventory_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}