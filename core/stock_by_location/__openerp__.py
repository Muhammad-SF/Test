# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 BrowseInfo(<http://www.browseinfo.in>).
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
    'name': 'Stocks By Location',
    'version': '1.1.3',
    'category': 'Warehouse',
    'sequence': 14,
    'price': '25',
    'currency': "EUR",
    'summary': '',
    'description': """
    -Stock Balance by Location
    -Stock Quantity by location
    -Location based stock
    -Display Product Quantity based on stock.
    -Warehouse stock based on location
    -Stock Quantity based on location
    -Stock by location
    -Stock qty by location
    -Stock location
""",
    'author': 'BrowseInfo',
    'website': 'http://www.browseinfo.in',
    'images': [],
    'depends': ['base','sale','stock', 'inventory_reserved_available_qty'],
    'data': [
        'product.xml',
    ],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
