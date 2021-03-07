# -*- coding: utf-8 -*-
{
    'name': 'Cash Flow Report',
    'version': '1.1.1',
    'category': 'Report',
    'sequence': 9,
    'summary': 'setup for cash flow report process',
    'description': "This module includes cash flow report process related setup",
    'website': 'http://www.axcensa.com/',
    'author': 'Axcensa',
    'depends': [
        'account_accountant','l10n_sg'
    ],
    'data': [
        'data/cash_flow_hierarchy_report_data.xml',
        'views/account_financial_report.xml',
        'report/cash_flow_statement_pdf.xml',
        'wizard/cash_flow_statement_xl.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}