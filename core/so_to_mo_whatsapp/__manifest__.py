# -*- coding: utf-8 -*-
{
    "name": "SO to MO Whatsapp Notification",
    "author": "HashMicro/ Amit Patel",
    "version": "1.1.2",
    "website": "www.hashmicro.com",
    "category": "mrp",
    'summary': 'SO to MO Whatsapp Notification',
    'description': """
    	This module help to send notification when so confirm based on the mrp configuration to users.
    """,
    "depends": [
        'mrp',
        'sale',
        'stock',
        'manufacturing_plan',
        'mrp_configuration',
        'so_to_mo',
        'chat_api_whatsapp',
    ],
    "data": [
        'views/mrp_setting_view.xml',
        'data/ir_config_parameter_data.xml',
    ],
    'demo': [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
