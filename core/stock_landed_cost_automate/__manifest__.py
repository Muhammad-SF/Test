# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
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
    'name': 'Automated Stock landed cost calculation',
    'version': '1.1.1',
    'summary': 'Calculate stock landed cost automatically when shipment received.',
    'description': """
		Automated calculation of stock landed cost, invoice landed cost, Stock landed cost based on picking, Stock landed-cost on picking. 
		Landedcost on invoice,stock landed cost on product, product landed cost, product stock landed cost, stock invoice landed cost, landed cost based on invoice, invoice calculation landed cost, Automated landed cost, automated picking landed cost.
    """,
    'author': 'BrowseInfo',
    "currency": "EUR",
    "price": 99,
    "category": "Warehouse",
    'website': 'http://www.browseinfo.in',
    'depends': ['base','purchase','stock_landed_costs','sale'],
    'data': ["account_invoice.xml",
             "purchase.xml"
    
             
             ],
	'qweb': [
		],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    "images":["static/description/Banner.png"],
}
