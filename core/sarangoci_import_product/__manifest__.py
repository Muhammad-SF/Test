# -*- coding: utf-8 -*-
{
    'name': "Sarangoci Import Product",

    'description': """
        Product
    """,
    'author': 'HashMicro / Quy',
    'website': 'www.hashmicro.com',

    'category': 'timesheet',
    'version': '1.1.1',

    'depends': ['product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/employee_sequence.xml',
        'views/product.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],
    'demo': [
    ],
}