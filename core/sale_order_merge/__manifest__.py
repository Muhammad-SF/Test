# coding: utf-8
{
    "name": "Merge sale orders",
    "summary": "Merge sale orders that are confirmed, invoiced or delivered",
    "version": "1.1.1",
    "category": "Sales Management",
    "website": "www.hashmicro.com",
    "author": "HashMicro / MP technolabs / Monali",
    "depends": [
        "sale_stock",
    ],
    "data": [
        "views/sale_order.xml",
        "wizard/sale_order_merge.xml",
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
