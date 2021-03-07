# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 OpenERP SA (<http://www.serpentcs.com>)
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name" : "Singapore - Accounting Reports",
    "version" : "1.1.1",
    "author" : "HashMicro",
    'category': 'Accounting & Finance/Account Reports',
    "website" : "http://www.hashmicro.com",
    "description": """
Singapore Accounting: QWeb reports of Account.
==============================================

Singapore accounting IRAS compliance report for

* Genertion of GST form 5 and GST form 7 reports as per official l10n_sg COA.

""",
    'depends': ['l10n_sg', 'sale', 'purchase', 'stock', 'report'],
    'demo': [],
    'data': [
             'data/gst_f5_report_config_data.xml',
             'security/security.xml',
             'security/ir.model.access.csv',
             'views/partner_view.xml',
             'views/gstreturn_f5_report_view.xml',
             'wizard/gstreturn_view.xml',
             'wizard/account_wizard_view.xml',
             'wizard/partner_aged_wiz_extended.xml',
             'views/account_balance_full_temp.xml',
             'views/report_menu.xml',
             'views/account_financial_report_view.xml',
             'views/gstreturn_f7_report_view.xml',
             'views/company_extended_view.xml',
             'wizard/gstreturnf7_view.xml',
             'wizard/e_tax_wiz_view.xml',
             'views/account_full_2_cols.xml',
             'views/account_full_4_cols.xml',
             'views/account_full_5_cols.xml',
             'views/account_full_qtr_cols.xml',
             'views/account_full_13_cols.xml',
             'views/trial_balance_temp.xml',
             'views/report_financial.xml',
             'views/account_tax_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
