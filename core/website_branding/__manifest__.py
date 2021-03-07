# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Website InterFace Branding',
    'version': '1.1.1',
    'category': 'Website',
    'summary': 'User interface',
    'description': """
    """,
    'author':'Hashmicro / Parikshit Vaghasiya',
    'depends': ['base','web','website'],
    'qweb': ['static/src/xml/*.xml'],
    'data': [
        'views/hm_system_website_view.xml',
    ],
    'installable': True,
    'auto_install': True,
}
