# -*- coding: utf-8 -*-
{
    'name': "stock_count_link_inv_adjust",

    'summary': """Read Only Field in Stock Count""",

    'description': """
        Read Only Field in Stock Count
            - Make Stock Count Progress State Count Qauntity Readonly
            - Forecast Overhead Cost
    """,

    'category': 'Stock',
    'version': '1.1.1',

    'depends': ['ops_app_stock_take'],

    'data': [
        'view/stock_count_view.xml',
    ],

}