# -*- coding: utf-8 -*-
{
    "name": "POS Synchronization for FNB",
    "author": "HashMicro/ Amit Patel",
    "version": "1.1.1",
    "website": "www.hashmicro.com",
    "category": "Point Of Sale",
    'summary': 'POS Synchronization for FNB',
    'description': """
        This module cover the following points:

        * Create default auditlog rule for Restaurant Floor and Table	
        * Add pos_sync_id field in Restaurant Floor and Table and it should be the combination of the Branch ID + POS + Record ID
        * Sync Restaurant Floor and Table using pos_sync_id and auditlogs.
        * Add Logs for Restaurant Floor and Table with the date and status[Success Or Failed]
        * Sync the Restaurant Floor and Table from the manual sycn using pos configuration and pos_sync_id
    """,
    "depends": [
        "std_pos_sync",
        "pos_restaurant",
        "pos_bus_restaurant",
        "pos_home_delivery",
        "pos_price_charges_calculation"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/auditlog_rule_data.xml",
        "views/restaurant_view.xml",
        "views/sync_log_view.xml",
        "views/pos_delivery_order_view.xml",
        "wizard/floor_sync_view.xml",
        "wizard/table_sync_view.xml",
    ],
    'demo': [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
