# -*- coding: utf-8 -*-
{
    'name': 'Update New Bom From Mc',
    'version': '1.1.1',
    'category': '',
    'author': 'Hashmicro/Janbaz Aga',
    'description': """
        Update materials on MC to BoM
    """,
    'website': 'http://www.hashmicro.com/',
    'depends': [
        'manufacturing_material_consumption',
    ],
    'data': [
        'security/material_security.xml',
        'views/mrp_material_consumed_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
