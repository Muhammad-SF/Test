# -*- coding: utf-8 -*-
{
    'name': "STD material Request",

    'summary': """
        Material Request is for users to request a certain product to his warehouse, which can be fulfilled by Internal transfer OR creating a purchase
        """,

    'description': """
        Material Request is for users to request a certain product to his warehouse, which can be fulfilled by Internal transfer OR creating a purchase
    """,

    'author': "Hashmicro / Balram",
    'website': "http://www.hashmicro.com",

    'category': 'Uncategorized',
    'version': '2.1.2',

    # any module necessary for this one to work correctly
    'depends': ['base','stock', 'stock_by_location', 
                'purchase_request', 'internal_transfer_receipt', 
                'inventory_approval_matrix','user_super_admin_access','warehouse_stock_restriction_extended',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/internal_transfer.xml',
        'views/purchase_request_wizard.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/configur.xml',
        'views/report_picking.xml',
        'wizard/show_material_done_popup_views.xml',
    ],
}
