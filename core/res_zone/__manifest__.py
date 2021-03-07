# -*- coding: utf-8 -*-
{
    'name': 'Res Zone',
    'version': '1.1.3',
    'category': '',
    'summary': 'Res Zone',
    'description': "Res Zone",
    'website': 'www.hashmicro.com',
    'author': 'HashMicro/Jaydeep',
    'depends': [
        'base', 'point_of_sale', 'branch', 'company_brand'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_zone_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
