# -*- coding: utf-8 -*-
{
    'name': "Lot/Serial Numbering in Manufacturing Work Order Manterial Consumption screen",

    'description': """

        Lot/Serial Numbering in Manufacturing Work Order Manterial Consumption screen

    """,

    'author': 'HashMicro / Dev (Braincrew Apps)',
    'website': 'https://www.hashmicro.com',

    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['manufacturing_material_consumption'],

    # always loaded
    'data': [
        'views/stock_view.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
 }
