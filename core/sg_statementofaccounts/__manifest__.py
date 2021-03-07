# -*- coding: utf-8 -*-
{
    'name': 'Sg Statementofaccounts',
    'version': '1.1.1',
    'category': 'Accounting',
    'sequence': 18,
    'summary': 'setup for customer statement of accounts report',
    'description': "This module includes setup to generate customer statement of accounts report",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kannan',
    'depends': [
        'account_accountant','sale'
    ],
    'data': [

        'report/customer_soa_report.xml',
        'report/invoice_header_footer.xml',
        'views/sale_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}