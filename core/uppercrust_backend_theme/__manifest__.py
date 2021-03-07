# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'EQUIP 10 Backend Theme',
    'category': "Themes/Backend",
    'version': '1.1.8',
    'summary': 'Customized Backend Theme',
    'description': 'Customized Backend Theme',
    'author': "HashMicro",
    'depends': ['web_planner', 'document','web'],
    'website': 'www.hashmicro.com',
    'data': [
        'data/theme_data.xml',
        'security/global_search_security.xml',
        'security/ir.model.access.csv',
        'views/search_config_view.xml',
        'wizard/global_search_batch_wizard_view.xml',
        'views/search_config_batch_view.xml',
        'views/webclient_templates.xml',
        'views/res_company_view.xml',
	'views/apps_menu.xml',
	'views/settings_menu.xml',
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'images': [
        'static/description/main_screen.png',
        'static/description/uppercrust_screenshot.jpg',
    ],
    'installable': True,
    'auto_install': True,
    'bootstrap': True,
    'application': True,
    'license': 'OPL-1',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

