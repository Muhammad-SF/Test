# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Supplier Portal',
    'category': 'Website',
    'summary': 'Add your supplier document in the frontend portal (RFQ, Purchase, Delivery,Invoices)',
    'version': '1.1.1',
    'description': """
Add your supplier document in the frontend portal. Your customers will be able to connect to their portal to see the list (and the state) of their invoices (pdf report), sales orders and quotations (web pages).
        """,
    'depends': [
        # 'portal_sale',
        'website_portal',
        'stock',
        'purchase'
        # 'website_payment',
    ],
    'data': [
        'views/website_portal_sale_templates.xml',
        'security/ir.model.access.csv',
        'views/purchase_order.xml',
    ],
    'demo': [
        # 'data/sale_demo.xml'
    ],
    'installable': True,
}
