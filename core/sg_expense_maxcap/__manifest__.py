# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
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
    "name" : "Hr Expense Maxcap",
    "version" : "1.1.1",
    "author" : "Serpent Consulting Services Pvt. Ltd.",
    'category': 'Human Resources',
    "website" : "http://www.serpentcs.com",
    "description": """
Manage Expense Reimbursement Maximum limit per Employee
========================================================
This module is used to add expense product and it's maximum amount limits configurations in employee's contract,
which use in expense claim by user.

* Max cap to each expense product & facility to override the max cap on each product for each employee.
""",
    'depends': ['hr_contract','hr_expense'],
    'data': [
             'security/ir.model.access.csv',
             'view/hr_contract_view_extended.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:`