# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'Uppercrust Debranding',
    'version': '1.1.1',
    'description': """ Debranding with Uppercrust Backend Theme
    """,
    'category': 'web',
    'summary': 'HashMicro Backend Theme',
    'author': 'HashMicro Ltd.',
    'website': 'www.hashmicro.com',
    'depends': ['base_setup', 'web', 'mail', 'web_planner', 'uppercrust_backend_theme', 'hm-front-end-theme', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'data/res_company_data.xml',
        'data/res_groups.xml',
        'views/sync_uppercrust_debranding_view.xml',
        'views/app_theme_config_settings_view.xml',
        'views/ir_model_view.xml',
        'views/module_view.xml',
    ],
    'qweb': [
        'static/src/xml/customize_user_menu.xml',
    ],
    'demo': [

    ],
    'license': 'OPL-1',
    'installable': True,
    'application': False,
    'auto_install': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
