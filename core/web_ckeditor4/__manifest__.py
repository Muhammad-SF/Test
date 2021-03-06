# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'CKEditor 4.x widget',
    'version': '1.1.1',
    'author': "Therp BV,Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/web',
    'summary': 'Provides a widget for editing HTML fields using CKEditor 4.x',
    "category": "Tools",
    'license': 'AGPL-3',
    "depends": [
        'web',
    ],
    'data': [
        'templates/assets.xml',
    ],
    'css': [
        'static/src/css/web_ckeditor4.css',
    ],
    'installable': True,
    'auto_install': False,
}
