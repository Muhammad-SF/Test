# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Restaurant Management - Reporting',
    'version': '1.1.1',
    'author': 'Serpent Consulting Services Pvt. Ltd., OpenERP SA',
    'website': 'http://www.serpentcs.com, http://www.openerp.com',
    'depends': ['hotel_restaurant', 'report_hotel_reservation'],
    'license': 'AGPL-3',
    'category': 'Generic Modules/Hotel Restaurant',
    'data': [
        'security/ir.model.access.csv',
        'views/report_hotel_restaurant_view.xml',
    ],
    'images': ['static/description/RestaurantReporting.png'],
    'installable': True,
    'auto_install': False,
}
