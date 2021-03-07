# -*- coding: utf-8 -*-
{
    'name': "Signature Management",

    'summary': """
        Enable digital signature for documents such as sale orders,
        purchase orders, invoices, payslips and procurement receipts.""",

    'description': """
        Enable digital signature for documents such as sale orders,
        purchase orders, invoices, payslips and procurement receipts.
    """,

    'author': "HashMicro/ Krupesh",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'web',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'purchase', 'account',
        'hr_payroll', 'credit_debit_note', 'web', ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/users_view.xml',
        'views/we_digital_sign_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
        'views/sale_report_templates.xml',
        'views/account_invoice_view.xml',
        'views/report_invoice.xml',
        'views/purchase_order_view.xml',
        'views/purchase_order_templates.xml',
        'views/purchase_quotation_template.xml',
        'views/hr_payroll_view.xml',
        'views/report_payslipdetails_templates.xml',
        'views/report_payslip_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb': ['static/src/xml/digital_sign.xml'],
}
