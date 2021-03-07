# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
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
    "name": "Singapore Income Tax report",
    "version": "1.1.1",
    "depends": ["l10n_sg_hr_payroll","hr_contract", "sg_hr_report"],
    "author" :"Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    "category": "Human Resources",
    "description": """
Singapore Income Tax reports.
============================
    - IR8A and IR8S esubmission txt file reports
    """,
    'data': ['security/group.xml',
             'security/ir.model.access.csv',
             'views/sg_income_tax_view.xml',
             'views/ir8a_form_report_view.xml',
             'views/ir8s_form_report_view.xml',
             'views/sg_income_tax_report_menu.xml',
             'wizard/emp_ir8a_text_file_view.xml',
             'wizard/emp_ir8s_text_file_view.xml',
             ],
    'installable': True,
    'auto_install':False,
    'application':True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: