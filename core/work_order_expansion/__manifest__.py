# -*- coding: utf-8 -*-
{
    'name': "Manufacturing Work Order Expansion",

    'description': """

        - Adding new tab Bill of Material on Work Order menu
        - Create Material Requests from Workorder form

    """,

    'author': 'HashMicro / Dev (Braincrew Apps)',
    'website': 'https://www.hashmicro.com',
    'category': 'Manufacturing',
    'version': '1.1.4',
    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'sequence/sequence.xml',
        'views/mrp_routing.xml',
        'views/mrp_workorder_view.xml',
        'views/mrp_workcenter_view.xml',
        'views/mrp_bom_line_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
 }
