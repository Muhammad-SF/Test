# -*- coding: utf-8 -*-
{
    'name': "survey_extended",

    
    'description': """
       The purpose of this module is to allow managers or administrators to create survey
    """,

    'author': "'HashMicro / MP technolabs / Prakash',",
    'website': 'https://www.hashmicro.com',

    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['survey'],

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