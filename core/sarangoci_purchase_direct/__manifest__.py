# -*- coding: utf-8 -*-
{
    'name' : 'Sarangoci Direct Purchase',
    'version' : '1.1.1',
    'category': 'Point of sale',
    'author': 'HashMicro / TechUltra Solutions / Krutarth /Jaydeep',
    'description': """This module allows to allow Purchase Direct
    """,
    'website': 'www.techultrasolutions.com',
    'depends' : ['purchase','stock','purchase_direct_website'],
    'data': [
        'data/sequence_data.xml',
        'views/res_partner_modifications.xml',
        'views/purchase_direct_modifications.xml',
        'views/templates.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
