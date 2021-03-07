    # -*- coding: utf-8 -*-

{
    'name': 'Account Modifications',
    'version': '1.1.1',
    'category': 'Account',
    'author': 'HashMicro / Purvi / Jaydeep',
    'website': 'www.hashmicro.com',
    'summary': 'Modifications in views and reports',
    'description': """

    """,
    'depends': ['base', 'web', 'account'],
    'data': [
    'views/account_view.xml',
    'wizard/account_aged_report_view.xml',
    'views/account.xml',
    ],
    'qweb': ["static/src/xml/account_move_line_quickadd.xml",],
}
