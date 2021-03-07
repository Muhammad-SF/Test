# -*- coding: utf-8 -*-
{
    'name': 'Transfer Activity Log',
    'version': '1.1.2',
    'category': 'Inventory',
    'sequence': 17,
    'summary': 'All transfer activity log report',
    'description': """Activity Log Report menu to analyze each transfer processed time (Draft to Done state), include
                        - Receiving Notes Activity Log
                        - Delivery Order Activity Log
                        - Transfer In Activity Log
                        - Transfer Out Activity Log
                      Available on PDF and XLS format.
                    """,
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kinjal(Laxicon Solution)/SetuConsulting',
    'depends': [
        'stock', 'inventory_extended', 'mail_extended'
    ],
    'data': [
        'data/scheduler_data.xml',
        'report/delivery_order_log_activity_tmpl.xml',
        'wizard/inventory_log_report_wiz_view.xml',
        'view/stock_picking_view.xml',
        'view/transfer_activity_log_report.xml',
    ],
    'qweb': [
        "static/src/xml/add_export_button.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
