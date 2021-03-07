# -*- coding: utf-8 -*-
{
    'name': 'Whatsapp Api Integration',
    'version': '1.1.1',
    'category': 'Message',
    'summary': 'Whatsapp Api Integration',
    'description': "Whatsapp Api Integration",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Jaydeep',
    'depends': ['mail','base'],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_blast_view.xml',
        'views/whatsapp_config_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}