# -*- coding: utf-8 -*-
{
    'name': "schedule_of_rates",

    'summary': """
         Allow users to configure the schedule of rates and tag to Contract """,

    'description': """
        Allow users to configure the schedule of rates and tag to Contract.
    """,

    'author': "Hashmicro / Duy",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Maintenance',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product','maintenance'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/job_order_view.xml',
    ],
    # only loaded in demonstration mode

}