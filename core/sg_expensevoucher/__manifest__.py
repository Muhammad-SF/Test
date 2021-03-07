# -*- coding: utf-8 -*-
{
    'name': 'Sg Expensevoucher',
    'version': '1.2.14',
    'category': 'Accounting',
    'sequence': 19,
    'summary': 'setup to customize account voucher',
    'description': "This module includes setup to customize account voucher and change menu name",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kannan, Goutham',
    'depends': [
        'account_voucher', 'approval_matrix_config'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/expensevoucher_security.xml',
        'views/res_config.xml',
        'views/income_expense_approving_matrix_view.xml',
        'views/account_voucher_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}