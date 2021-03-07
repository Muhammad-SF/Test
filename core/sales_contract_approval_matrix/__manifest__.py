# -*- coding: utf-8 -*-
{
    'name': "Sales Contract Approval Matrix",

    'description': """

        Configure approval matrix for sales contract.

    """,

    'author': 'HashMicro / Dev (Braincrew Apps)',
    'website': 'https://www.hashmicro.com',

    'category': 'Uncategorized',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['stable_account_analytic_analysis', 'contract_number', 'stable_hr_timesheet_invoice', 'sales_team'],

    # always loaded
    'data': [

        'data/sales_contract_approval_email_template.xml',
        'views/sales_contract_approval_matrix_view.xml',

        'wizard/contract_reject_reason_view.xml',

    ], # only loaded in demonstration mode
    'demo': [],
 }

