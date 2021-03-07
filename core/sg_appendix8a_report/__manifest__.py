# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011-2012 Serpent Consulting Services Pvt. Ltd. (<http://serpentcs.com>).
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
    "name": "Singapore Appendix8a report",
    "version": "1.1.1",
    "depends": ["sg_income_tax_report"],
    "author" :"Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    "category": "Human Resources",
    "description": """
Singapore Income Tax report.
============================
    - APPENDIX8A esubmission txt file reports
    - Module will add all the information fields to generate APPENDIX8A report
    - All fields will be added in employee contract based on sections as per IRAS rules.
    """,
    'data': [
             "views/sg_income_tax_extended_view.xml",
             "views/sg_appendix8a_report_view.xml",
             "views/sg_appendix8a_report_menu.xml",
             "wizard/emp_appendix8a_text_file_view.xml",
    ],
    'installable': True,
    'auto_install':False,
    'application':True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: