# -*- coding: utf-8 -*-
{
    'name': 'Sg Setup',
    'version': '1.1.1',
    'category': 'Sg Setup',
    'sequence': 1,
    'summary': 'Sg setup changes in Singapore - Accounting',
    'description': "This module includes changes required for Singapore - Accounting",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro / Axcensa',
    'depends': ['l10n_sg','base'],
    'data': [
        'data/currency_data.sql',
    ],
    'installable': True,
    'auto_install': False,
}