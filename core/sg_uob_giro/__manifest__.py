# -*- coding: utf-8 -*-
{
    'name': 'Singapore - UOB bank giro',
    'version': '1.1.1',
    'description': """
Singapore UOB bank giro file:
==============================================

Singapore UOB bank giro file generation :

* Generation of UOB bank giro file for salary payment.

""",
    'author': 'Hashmicro / Saravanakumar',
    'category': 'Localization/Account Reports',
    'website': 'https://www.hashmicro.com/',
    'depends': ['base', 'account', 'sg_hr_employee'],
    'data': [
        'wizard/uob_bank_specification_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
