# -*- coding: utf-8 -*-
{
    'name': 'Sales Subscriptions',

    'summary': 'Subscriptions management and recurring invoicing ',

    'description': """
Subscription Contract
  """,
    'author': 'DarbTech, HashMicro / Vu',
    'website': 'https://darbtech.net',
    'support': 'support@darbtech.net',
    'category': 'Sales',
    'version': '1.1.1',
    'price': 99.99,
    'currency': 'EUR',
    'images': ['static/sales_subscription.png'],

    'depends': [
        'sale',
        'subscription',
    ],

    'data': [
        # 'security/ir.model.access.csv',
        'views/sales_subscription_views.xml',
    ],
}
