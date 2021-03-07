# -*- coding: utf-8 -*-
{
    'name': 'Standard Sales Access Right',
    'version': '1.1.1',
    'author': "HashMicro / Maulik (Braincrew Apps) / Jeel",
    'category': 'Sale',
    'summary': '',
    'depends': ['base', 'sale', 'sales_team', 'crm'],
    'description': """
        create access right for sales
    """,
    "website": "https://www.hashmicro.com/",
    "data": [
        'security/sales_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/sale_order_view.xml',
    ],
    "installable": True,
    "auto_install": False,
}