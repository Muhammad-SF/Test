# -*- coding: utf-8 -*-
{
    'name': "Sales Analysis Extended",
    'summary': """
        Add SO Number and Invoice Numbers in Sales Analysis report""",
    'description': """
        Add SO Number and Invoice Numbers in Sales Analysis report
    """,
    'author': "Hashmicro/SetuConsulting",
    'website': "www.hashmicro.com",
    'category': 'sale',
    'version': '1.1.2',
    'depends': ['sale','sale_stock', 'product_brand', 'branch'],
    # always loaded
    'data': [
        'views/sale.xml',
        'reports/sale_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
