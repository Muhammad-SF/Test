# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
    'name': 'Scrap Report',
    'version': '1.1.1',
    'category': 'stock',
    'description': """

===================================================================================================================


""",
    'author': 'HashMicro / Shivam Dudhat',
    'website': '',
    'depends': [
        'stock',
        'scrap_extension',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/scrap_report_template.xml'
    ],
    'installable': True,
    'auto_install': False,
}
