# -*- coding: utf-8 -*-
{
    'name': 'SBC Modifier Student Portal',
    'version': '1.1.1',
    'category': 'school',
    'sequence': 7,
    'summary': 'setup for school student access rights',
    'description': "This module includes setup for school student access rights in school management process.",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kannan',
    'depends': [
        'school_assignment_ems','donation_management','reusable_studentProfile_resetdraft'
    ],
    'data': [
        'views/assignment_view.xml',
        'views/donation_management_view.xml',
        'views/school_fees_view.xml',
        'views/school_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}