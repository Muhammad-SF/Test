 # -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
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
    'name': 'Odoo 10 Sales Commission Based on Target',
    'version': '1.1.3',
    'category': 'Sales',
    'sequence': 2,
    'summary': 'Odoo Sales commission now you can easily Manage Complex Commission or Incentive Plans to based on Goals and Targets assign to a team or a sales man.',
    'description': """ Odoo Sales commission now you can easily Manage Complex Commission or Incentive Plans to based on Goals and Targets assign to a team or a sales man, Our Sales incentive module helps sales teams get a clear view into their incentives through automated commission reporting, ensuring that sales reps understand their incentives and are aligned with business goals. """,
    'author': 'HashMicro/Viraj',
    'website': 'https://www.globalteckz.com',
    "price": "99.00",
    "currency": "EUR",
    'images': ['static/description/Banner.png'],
    'depends': ['base','sale','account','account_accountant'],
    'data': [
        'view/sale_commission_view.xml',
        'view/sale_commission_report.xml',
        'view/sale_order.xml',
        'view/sales_team_view.xml',
        'wizard/sale_commission_report_wizard.xml',
        'report/sale_commission_report.xml',
        'report/sale_commission_report_template.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
