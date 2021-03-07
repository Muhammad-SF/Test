# -*- coding: utf-8 -*-
{
    'name': "SG Currency",

    'summary': """
        Update Currency for SGD""",

    'description': """
        settings for sg currency Module

        - In settings > Companies > 'Currency Update configuration' Tab.

        - Select 'Automatic update' then Add 'Webservice to use' and 'Currencies to update with this service'.

        This Module contains fileds to get update for currency form the Monetary Authority of Singapore
        and update the currency daily.
    """,

    'author': "HashMicro / Vu",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Financial Management/Configuration',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'currency_rate_update',
    ],

    # always loaded
    'data': [
        'data/currency.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}