# -*- coding: utf-8 -*-
{
    'name': "Tenant Management",

    'author': "Nikhil" ,
    'website': "http://www.yourcompany.com",

    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hm_visitor'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ]
}