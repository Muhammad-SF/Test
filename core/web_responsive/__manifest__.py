# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Web Responsive",
    "summary": "It provides a mobile compliant interface for Odoo Community "
               "web",
    "version": "1.1.1",
    "category": "Website",
    "website": "https://laslabs.com/",
    "author": "LasLabs, Tecnativa, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "installable": True,
    'auto_install': False,
    "depends": [
        'web'
    ],
    "data": [
        'views/assets.xml',
        'views/web.xml',
    ],
}
