# -*- coding: utf-8 -*-
{
    'name': "Stock Transport Management",
    'version': '1.1.1',
    'summary': """Manage Stock Transport Management With Ease""",
    'description': """This Module Manage Transport Management Of Stocks""",
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Tools',
    'depends': ['base', 'sale', 'stock', 'report_xlsx'],
    'data': [
        'views/transport_vehicle_view.xml',
        'views/transport_vehicle_status_view.xml',
        'views/transportation_sale_order_view.xml',
        'views/transport_warehouse_view.xml',
        'views/transport_wizard_view.xml',
        'views/transport_report.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
