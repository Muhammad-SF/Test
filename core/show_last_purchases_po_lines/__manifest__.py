# -*- coding: utf-8 -*-
{
    'name': 'Show Last Purchases Po Lines',
    'version': '1.1.1',
    'category': 'Purchase',
    'author': 'HashMicro / Uday',
    'summary': """
                Show Last Purchases Po Lines""",

    'description': """Show Last Purchases Po Lines
    """,
    'website': 'www.hashmicro.com',
    'depends': ['base','purchase'],
    'data': [
            'security/ir.model.access.csv',
            'views/po_line.xml',
        ],
}
