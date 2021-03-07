# -*- coding: utf-8 -*-
{
    'name': "pos_sync_button_action",
    'summary': """
        sarangoci_pos_sync_button_action""",
    'description': """
        pos_sync_button_action
    """,
    'author': "HashMicro/ Viet",
    'website': "http://www.hashmicro.com",
    'category': 'POS',
    'version': '1.1.1',
    'depends': [
        'pos_pull_and_push_product',
        'pos_send_order'
    ],
    'data': [
        'views/views.xml',
        'views/cron.xml'
    ],
}