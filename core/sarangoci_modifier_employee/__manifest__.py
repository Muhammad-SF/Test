# -*- coding: utf-8 -*-
{
    'name': "Sarangoci Modifier Employee",

    'description': """
        This module change something in employee form
    """,
    'author': 'HashMicro / Quy',
    'website': 'www.hashmicro.com',

    'category': 'hr',
    'version': '1.1.1',

    'depends': ['base', 'hr','sg_hr_employee','hr_employee_loan'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/employee_sequence.xml',
        'views/hr_employee_view.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],
    'demo': [
    ],
}