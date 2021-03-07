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
    "name": "sg Reports",
    "version": "1.1.1",
    "depends": ["base", 'sg_holiday_extended', 'l10n_sg_hr_payroll','sg_hr_report','sg_income_tax_report'],
    "author" :"Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    "category": "Report",
    "description": """
Singapore Form IR21 report.
============================
    - Generate IR21 pdf file report
    """,
    "data":[
             'views/res_company_extended_view.xml',
             'views/hr_employee_extended_view.xml',
             'wizard/form_ir21_wizard_report.xml',
             'report/angcrane_report.xml',
             'report/report.xml',
             ],
    'installable': True,
    'auto_install':False,
    'application':False,
}
