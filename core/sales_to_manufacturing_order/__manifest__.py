# -*- coding: utf-8 -*-
{
    'name' : 'Sale Order to Manufacturing',
    'version' : '1.1.1',
    'category': 'Production',
    'description': 'Link manufacturing order to related sale order',
    'summary': 'Link manufacturing order to related sale order',
    'author': 'HashMicro/Rawish/Maulik Deven',
	'website': 'www.hashmicro.com',
    'depends' : ['sale_mrp', 'manufacturing_plan_extended'],
    'data': ['views/sale_mrp_view.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
