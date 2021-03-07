# -*- coding: utf-8 -*-
{
    'name': "Termination Payslip",

    'summary': """
        Show indication or cessation date at employee payslip when employment status=In Notice or Terminated.""",

    'description': """
        Show indication or cessation date at employee payslip when employment status=In Notice or Terminated.
    """,

    'author': "HashMicro/ Krupesh",
    'website': "https://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll', 'hm_hr_sg_standardization', ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/hr_payslip_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
