# -*- coding: utf-8 -*-
{
    'name': "RFQ Check Stock",

    'summary': """
        Feature for check product stock in RFQ order line""",

    'description': """
        Feature for check product stock in RFQ order line
    """,

    'author': "Hashmicro",
    'website': "http://www.hashmicro.com",

    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','sale','product',
                'stock','inventory_reserved_available_qty', 
                'stock_by_location'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/views.xml',
    ],
}