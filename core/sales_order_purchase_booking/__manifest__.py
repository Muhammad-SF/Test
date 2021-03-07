# -*- coding: utf-8 -*-
{
    'name' : 'Purchase From Booking Order',
    'version' : '1.1.1',
    'category': 'Purchase',
    'description': 'Create purchase order from booking',
    'summary': 'Create purchase order from booking',
    'author': 'HashMicro/Yogesh',
	'website': 'www.hashmicro.com',
    'depends' : ['purchase','product_booking'],
    'data': ['views/booking_order.xml'],
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
