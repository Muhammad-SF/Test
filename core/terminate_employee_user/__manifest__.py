# -*- coding: utf-8 -*-
{
    'name': "terminate_employee_user",

    'summary': """
        System will auto update the employment status to Terminated and inactive the user.""",

    'description': """
        System will auto update the employment status to Terminated and inactive the user.
    """,

    'author': "Teksys Enterprise Pvt. Ltd. / Rajnish",
    'website': "http://www.teksys.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
    ],
}