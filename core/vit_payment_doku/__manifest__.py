# -*- coding: utf-8 -*-

{
    'name': 'DOKU Payment Acquirer',
    'category': 'Accounting',
    'summary': 'DOKU Acquirer: DOKU Implementation',
    'version': '1.1.1',
    'description': """DOKU Payment Acquirer""",
    'depends': ['payment'],

    'images': ['static/description/images/main_screenshot.jpg'],
    'price': '200',
    'currency': 'USD',
    'license': 'OPL-1',
    'summary': 'This is modul is used to acquire online payment using DOKU payment systems',
    'author':'Akhmad D. Sembiring [vitraining.com]',
    'website':'http://vitraining.com',
    'data': [
        'views/payment_views.xml',
        'views/payment_doku_templates.xml',
        'views/account_config_settings_views.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
}
