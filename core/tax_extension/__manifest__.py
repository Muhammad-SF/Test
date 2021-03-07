# -*- coding: utf-8 -*-
{
    'name': 'Tax Extension',
    'version': '1.1.2',
    'category': 'Accounting',
    'sequence': 16,
    'summary': 'Tax Extension',
    'description': "Tax Extension",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Jaydeep',
    'depends': [
        'account','sale','purchase','account_cancel','account_accountant'
    ],
    'data': [
        # 'data/data.xml',
        # 'wizard/int_cb_transfer_wizard_view.xml',
          'views/account_view.xml',
          'views/sale_view.xml',
          'views/purchase_view.xml',
          
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}