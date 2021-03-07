# -*- coding: utf-8 -*-
{
    'name': "SO Progress Billing Calculation",

    'description': """

        User can generate customer invoice using Progress Billing % or Retention Rate method from Sales Order.

    """,

    'author': 'HashMicro / Dev (Braincrew Apps)',
    'website': 'https://www.hashmicro.com',

    'category': 'Uncategorized',
    'version': '1.1.2',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'cost_sheet_progress_billing'],

    # always loaded
    'data': [

        'data/product.xml',

        'views/sale_view.xml',
        'wizard/sale_make_invoice_advance_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
 }