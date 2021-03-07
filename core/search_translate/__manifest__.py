# -*- coding: utf-8 -*-
{
    'name': "search_translate",

    'summary': """
        Google translate search""",

    'version' : '1.1.1',
    'author': 'HashMicro / Viet',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    "external_dependencies": {'python': ['googletrans']},
}