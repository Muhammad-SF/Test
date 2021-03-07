# -*- coding: utf-8 -*-

{
    'name': 'signature_do_printout',
    'author': "Acespritech Solutions pvt.ltd",
    "version": "1.1.1",
    'description': """
    	This module add filter state,city,brand,promo cod in sales anyalysis report:
    """,
    
    'depends': ['base', 'purchase','stock'],
    'data': [
        'views/do_slip.xml'
    ],
    'demo': [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
