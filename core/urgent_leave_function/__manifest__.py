# -*- coding: utf-8 -*-
{
    'name': 'Urgent Leave',
    'version': '1.1.1',
    'category': 'Leave Management',
    'sequence': 13,
    'summary': 'setup for urgent leave request',
    'description': "This module includes setup for urgent leave request by overriding leave days limit function",
    'website': 'http://www.axcensa.com/',
    'author': 'Axcensa',
    'depends': [
        'leave_days_limit','sg_hr_holiday'
    ],
    'data': [
        'views/hr_holidays_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}