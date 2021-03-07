# -*- coding: utf-8 -*-
{
    "name": """Sync POS orders across multiple sessions""",
    "version": "1.1.1",
    "summary": """Use multiple POS for handling orders""",
    "category": "Point Of Sale",

    "author": "TechnoSquare",
    "support": "info@technosquare.in",
    "website": "http://technosquare.in/",

    "depends": [
        "bus",
        "point_of_sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/templates.xml",
        "views/pos_config_views.xml",
    ],
    "demo": [
        "demo/demo.xml",
    ],
    "qweb": [
        "static/src/xml/pos_longpolling_connection.xml",
        "static/src/xml/sync_pos_orders.xml",
    ],
    'images': ['static/description/banner.jpg'],
    'live_test_url': 'https://youtu.be/P35HxGU9THA',
    'price': 80,
    'currency': "EUR",
    "auto_install": False,
    "installable": True,
}
