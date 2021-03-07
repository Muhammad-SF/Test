# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Sales Blanket Order',
    'version': '1.1.1',
    'category': 'Sales',
    'author': 'Hashmicro/ MPTechnolabs(Chankya)',
    'website': "http://www.hashmicro.com",
    'company': 'Hashmicro',
    'description': """
This module allows you to manage your Sales Blanket Order.
===========================================================

When a sale order is created, you now have the opportunity to save the
related blanket. This new object will regroup and will allow you to easily
keep track and order all your sales orders.
""",
    'depends' : ['sales_team', 'stock'],
    'demo': ['data/sale_requisition_demo.xml'],
    'data': [
        'security/sale_tender.xml',
        'security/ir.model.access.csv',
        'data/sale_requisition_data.xml',
        'views/sale_requisition_views.xml',
        'report/sale_requisition_report.xml',
        'report/report_salerequisition.xml',
    ],
}
