# -*- coding: utf-8 -*-
{
    'name': "Manufacturing Disassemble",
    'description': "This module will helps to disassemble the products",
    'summary': 'Disassembling the products',
    'author': "HashMicro / Saravanakumar / Sang",
    'website': "www.hashmicro.com",
    'category': 'Product',
    'version': '1.1.1',
    'depends': [
        'base',
        'stock_account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/disassemble_data.xml',
        'views/res_disassemble_views.xml',
        'views/res_assemble_views.xml',
        'views/product_template_views.xml',
    ],
    'application': True
}