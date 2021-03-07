# -*- coding: utf-8 -*-
# Copyright 2018 Giacomo Grasso <giacomo.grasso.82@gmail.com>
# Odoo Proprietary License v1.0 see LICENSE file

{
    'name': 'Treasury and Cash Flow Management',
    'version': '1.1.1',
    'description': """
            Treasury and cash flow management features for Odoo.
        """,
    'author': 'Giacomo Grasso - giacomo.grasso.82@gmail.com, '
              'Gabriele Baldessari - gabriele.baldessari@gmail.com',
    'maintainer': 'Giacomo Grasso - giacomo.grasso.82@gmail.com',
    'price': 135.00,
    'currency': 'EUR',
    'website': 'https://github.com/jackjack82',
    'images': ['static/description/main_screenshot.png'],
    'license': 'OPL-1',
    'depends': [
        'account',
        'account_accountant',
        'base',
        ],
    'data': [
        'views/account_account.xml',
        'views/account_bank_statement.xml',
        'views/account_invoice.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
        'views/treasury_menu.xml',
        'views/treasury_forecast.xml',
        'views/treasury_bank_forecast.xml',
        'views/treasury_forecast_template.xml',
        'views/res_config_view.xml',

        'security/access_rules.xml',
        'security/ir.model.access.csv',

        'wizard/wizard_mass_edit.xml',
    ],

    'installable': True,
    'auto_install': False,
}
