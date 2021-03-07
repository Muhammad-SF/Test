# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    "name" : "Singapore Employee Extension",
    "version" : "1.1.3",
    "author" : "Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    "category": "Human Resources",
    "description" : 
    '''
    Module to manage Employee information.
    ''',
    "depends" : ["hr_holidays","hr_expense", "hr_attendance", "hr_payroll", "hr_timesheet"],
    "init_xml": [],
    "data": [
        "security/security.xml",
        "views/hr_employee_view.xml",
        "views/resources.xml",
        "views/employee_race_view.xml",
        "security/ir.model.access.csv",
        "views/hr_extended_menu.xml",
        "report/employee_info_report_view.xml",
        "data/employee_paperformat.xml",
    ],

    "installable": True,
    "auto_install": False,
    "application": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
