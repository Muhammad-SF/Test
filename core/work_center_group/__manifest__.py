# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
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
    'name': 'Work Center Grouping',
    'summary': 'Work Center Grouping',
    'author': 'HashMicro / Shivam',
    'license': 'AGPL-3',
    'website': 'http://www.laxicon.in',
    'images': [],
    'category': 'Manufacturing',
    'version': '1.1.2',
    'description': """
    1. Create a new object called “Work Center Groups”, add this as a menu item under Manufacturing > Operations
    2. Fields for Work Center Groups:
        a. Group Name: Textfield
        b. List of Work Centers (Add a list of work centers where users can add multiple work centers in a work center group)
    3. In Routing, add a field called “Work Center Group” in “Work Center Operations” of the Routing, which is a reference to the object above, and remove the Work Center Field
    4. When a Manufacturing Order starts to create the work order, instead of a fixed work center, it will use one of the work center in the work center group where:
        a. The one that is free (no work order in process)
        b. If there is none that is free, use the work order that has the earliest deadline based on the total work order durations

    """,
    'depends': ['mrp','work_order_expansion'],
    'data': [
        'security/ir.model.access.csv',
        'views/work_center_group_view.xml',
        'views/mrp_routing_view.xml',
        'views/mrp_work_order_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
