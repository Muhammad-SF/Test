# -*- coding: utf-8 -*-
{
    'name': "User Po Rate",

    'summary': """
        User Po Rate""",

    'description': """
        User Po Rate
    """,

    'author': "HashMicro/Kishan Chotaliya/Antsyz-Kannan",
    'website': "http://www.hashmicro.com",
    'category': 'Uncategorized',
    'version': '1.3.21',
    'depends': ['purchase_order_payment_with_down_payment', 'currency_converter', 'discount_purchase_order', 'sale', 'spot_rate_register_payment'],
    'auto_install': True,
    'data': [
        'views/invoice_view.xml',
        'views/purchase_views.xml',
        'views/currency_view.xml',
        'views/res_config_view.xml',
        'views/sale_view.xml',
    ],
    'demo': [
    ],
}

