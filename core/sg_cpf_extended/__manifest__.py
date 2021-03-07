# -*- coding: utf-8 -*-
#############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://serpentcs.com>).
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
#############################################################################

{
    "name": "SG CPF Extended",
    "version": "1.1.1",
    "author": "Serpent Consulting Services Pvt. Ltd.",
    "description": """A module worked for cpf where allowances are devided in category of aw & ow similarly applied improve reports for ir8a & ir8s.""",
    "images": [],
    "license": "",
    "website": "http://www.serpentcs.com, http://www.openerp.com",
    "depends": ["sg_income_tax_report"],
    "category": "Generic Modules/SG Custom Features",
    "data": [
             'security/hr.salary.rule.category.csv',
             'views/sg_custom_view.xml',
             'data/salary_structure.xml',
             'views/ir8s_form_report_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
