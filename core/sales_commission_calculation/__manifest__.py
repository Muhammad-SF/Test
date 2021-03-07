# -*- coding: utf-8 -*-
{
    'name': "Sales Commission Calculation",

    'summary': """
        sales_commission_calculation""",

    'description': """
        sales_commission_calculation
    """,

    'author': "Hashmicro / Ankur",
    'website': "www.hashmicro.com",

    'category': 'Sales',
    'version': '1.2.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'sales_team',
        'product',
        'sale',
        'account',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/commission_scheme_views.xml',
        'views/crm_team_views.xml',
        'views/commission_views.xml',
        'views/commission_scheme_salesperson.xml',
        'views/commission_scheme_salesteamleader.xml',
        'views/interval_commission_views.xml',
	'wizard/commission_wizard_view.xml',
    ],
    'application': True,
}
