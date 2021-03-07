# -*- coding: utf-8 -*-

# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Sale Receipt Ext',
    'version' : '1.1.1',
    'summary': 'Manage your debts and credits thanks to simple sale/purchase receipts',
    'description': """
TODO

old description:
Invoicing & Payments by Accounting Voucher & Receipts
=====================================================
The specific and easy-to-use Invoicing system in Odoo allows you to keep track of your accounting, even when you are not an accountant. It provides an easy way to follow up on your vendors and customers.

You could use this simplified accounting in case you work with an (external) account to keep your books, and you still want to keep track of payments.

The Invoicing system includes receipts and vouchers (an easy way to keep track of sales and purchases). It also offers you an easy method of registering payments, without having to encode complete abstracts of account.

This module manages:

* Voucher Entry
* Voucher Receipt [Sales & Purchase]
* Voucher Payment [Customer & Vendors]
    """,
    'category': 'Accounting',
    'sequence': 20,
    'website' : 'https://www.odoo.com/page/billing',
    'depends' : ['account_voucher'],
    'demo' : [],
    'data' : ['views/sales_receipt_view.xml',
              'report/report_sale_receipt_view.xml',
              'report/report_salesreceipt.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
