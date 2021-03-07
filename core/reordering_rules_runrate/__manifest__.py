# -*- coding: utf-8 -*-

{
    "name": "Reordering Rules Runrate",
    'summary': """
            Reordering Rules Runrate
        """,
    'description': """
        Reordering Rules Runrate
        - 1.1.1 to 1.1.2 (Kinjal)
            - as per documentation https://docs.google.com/presentation/d/174B68iOi1wiRG-D3PPqmfX7pFPOCfYgMQR1zAkm5NQY/edit#slide=id.g7854d6e49f_0_0
    """,
    "version": "1.1.2",
    "category": "",
    "author": "Hashmicro / Uday / Kinjal",
    "website": "http://www.hashmicro.com",
    "depends": ['base', 'stock', 'reordering_rule_extended', 'product_usage', 'transfer_activity_log'],
    "data": [
           'views/stock_warehouse_orderoint_view.xml',
           'data/reordering_rules_data.xml',
    ],
}
