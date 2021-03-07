# -*- coding: utf-8 -*-
{
    'name': "Purchase Access Right Groups",
    'summary': """Standard access for Purchase Users""",
    'description': """Include Purchase Request Access Rights""",
    'author': "Hashmicro / Antsyz-Muthulakshmi",
    'website': "www.hashmicro.com",
    'category': 'Purchase Access',
    'version': '1.1.1',
    'depends': ['base', 'purchase', 'purchase_request', 'purchase_request_to_rfq', 'approving_matrix_configuration',
                'purchase_requisition', 'approving_matrix_pr', 'product', 'stock'],
    'data': [
        'security/purchase_request_group.xml',
        'security/ir.model.access.csv',
        'views/purchase_views.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True
}
