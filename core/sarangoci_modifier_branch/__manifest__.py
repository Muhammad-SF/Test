# -*- coding: utf-8 -*-
{
    'name': "sarangoci_modifier_branch",


    'description': """
        Service charge in branch
    """,
    
    'author': 'HashMicro / MP technolabs / Prakash',
    'website': 'www.hashmicro.com',

    'category': 'pos',
    'version': '1.1.1',


    # any module necessary for this one to work correctly
    'depends': ['branch'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}