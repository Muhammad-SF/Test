# -*- coding: utf-8 -*-
{
    'name': "supplier_rating",
    'summary': """
        supplier rating""",
    'description': """
        supplier rating
    """,
    'author': "HashMicro / MpTechnolabs - Bipin Prajapati",
    'website': "http://www.hashmicro.com",
    'category': 'HashMicro',
    'version': '1.1.1',
    'depends': [
        'sale',
        'purchase',
    ],
    # always loaded
    'data': [
        'views/supplier_rating_view.xml',
        'data/ir_sequence_data.xml',
        'data/rating_conf_demo.xml',
        'views/rating_configuration_view.xml',
        'views/supplier_rating_report.xml',
        'views/res_partner_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}