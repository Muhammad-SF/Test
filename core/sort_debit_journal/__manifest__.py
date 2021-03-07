# -*- coding: utf-8 -*-
{
    "name": "Sort Debit Journal",
    "version": "1.1.1",
    "author": "hashmicro/Antsyz-Kannan",
    "sequence": 54,
    "category": "Account",
    'website': 'http://www.hashmicro.com',
    "description": """
		To sort Journal Entries line table base on debit.
	""",
    "depends": [
        'account'
    ],
    "data": [
        'views/account_move_view.xml'
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
