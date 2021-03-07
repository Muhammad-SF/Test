# -*- coding: utf-8 -*-
{
    'name': "Accounting Analysis",

    'summary': """
Accounting analysis with Pivot and Graph""",

    'description': """
Summary
=======
This application provides dynamic accounting reports and analysis in form of pivot and graph views

With this module, you will have a depth analysis of your different financial accounts, analytic accounts. It also provides a treasury report.

Key Features
============

1. Journal Entries Analysis
   - Measures

     * Debit
     * Credit
     * Balance
     * Number of Entries
     * Product Quantity
  
   - Analysis

     * Account Payable Analysis (with Due Date factor)
     * Account Receivable Analysis (with Due Date factor)
     * Entries Analysis by Account
     * Entries Analysis by Account Type
     * Entries Analysis by Product
     * Entries Analysis by Partner
     * Entries Analysis by Currency (in multi-currency environment)
     * Entries Analysis by Company (in multi-company environment)
     * Entries Analysis by Journal
     * Entries Analysis by Analytic Account
     * Entries Analysis by Date
    
2. Treasury Analysis

   - Measures

     * Debit
     * Credit
     * Balance
     
   - Analysis
   
     * Treasury Analysis by Company (in multi-company environment)
     * Treasury Analysis by Journal
     * Treasury Analysis by Entry
     * Treasury Analysis by Partner
     * Entries Analysis by Date

2. Analutics Entries Analysis

   - Measures

     * Amount / Balance
     * Unit Amount
     * Number of Entries
     
   - Analysis

     * Entries Analysis by Account
     * Entries Analysis by General Account
     * Entries Analysis by Date
     * Entries Analysis by Product
     * Entries Analysis by Partner
     * Entries Analysis by Currency (in multi-currency environment)
     * Entries Analysis by Company (in multi-company environment)
     * Entries Analysis by User
   
Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,

    'author': "T.V.T Marine Automation (aka TVTMA)",
    'website': 'https://www.tvtmarine.com',
    'live_test_url': 'https://v10demo-int.erponline.vn',
    'support': 'support@ma.tvtmarine.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/account_entries_analysis.xml',
        'views/account_treasury_report.xml',
        'views/account_analytic_entries_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'images' : ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 49.5,
    'currency': 'EUR',
    'license': 'OPL-1',
}