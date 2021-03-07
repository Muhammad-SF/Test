# -*- coding: utf-8 -*-
##############################################################################
#
#    
#    See LICENSE file for full copyright and licensing details.
#
##############################################################################
{
	"name": "Giro Custom",
	"version": "1.1.1",
	"depends": [
		"account_accountant",
		"account_voucher"
	], 
	"author": "akhmad.daniel@gmail.com", 
	"category": "Accounting",
	"website": 'http://www.vitraining.com',
	"data": [
		"menu.xml", 
		"view/giro.xml",
		"view/invoice.xml",
	],
    'installable': True,
    'auto_install': False,
	"application": True,
}