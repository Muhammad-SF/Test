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
    "name": "Sg Report Letter Undertaking",
    "version": "1.1.1",
    "depends": ["base", 'sg_holiday_extended','sg_hr_report'],
    "author" :"Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    "category": "Report",
    "description": """
Singapore Letter Undertaking report.
============================
    - Generate Letter Undertaking pdf file report
    """,
    "data":[
             'wizard/wizard_letter_undertaking_view.xml',
             'report/sg_report.xml',
             'report/sg_report_letter_undertaking.xml',
             ],
    'installable': True,
    'auto_install':False,
    'application':False,
}
