# -*- coding: utf-8 -*-
{
    'name': 'Timesheet Leave',
    'summary': """Link leave history to timesheet module.""",
    'description': """Link leave history to timesheet module.""",
    "author": u"HashMicro / Abulkasim Kazi",
    "website": u"www.hashmicro.com",
    "version": '1.1.1',
    'category': 'HR',
    'depends': ['hr_timesheet_sheet', 'hr_timesheet_attendance', 'hr_holidays','sg_hr_holiday'],
    'data': [
        'views/hr_timesheet_sheet.xml',
    ],
    'demo': [],
    'images': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}
