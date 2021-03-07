# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 OpenERP SA (<http://www.serpentcs.com>)
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
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
    "name" : "Singapore - DBS bank giro",
    "version" : "1.1.1",
    "author" : "Serpent Consulting Services Pvt. Ltd.",
    'category': 'Localization/Account Reports',
    "website" : "http://www.serpentcs.com",
    "description": """
Singapore DBS bank giro file:
==============================================

Singapore dbs bank giro file generation :

* Generation of DBS bank giro file for salary payment.

""",
    'depends': ['sg_hr_report'],
    'data': [
             'views/res_partner_bank_view_extended.xml',
             'wizard/dbs_bank_specification_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:`