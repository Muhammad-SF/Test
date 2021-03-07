# -*- coding: utf-8 -*-
{
    'name': "Employee Working Schedule Variation Calendar",
    'description': """
    Create new working schedule interval variation (including daily, weekly and monthly)
    """,
    'author': 'HashMicro / Paras Sutariya',
    'website': 'https://www.hashmicro.com',
    'category': 'HR',
    'version': '1.1.2',
    'depends': [
        'hr_contract',
        'resource',
        'sg_holiday_extended',
        'hr_attendance',
        'web_calendar',
        'hr_payroll',
        'working_schedule_calendar'
    ],
    'data': [
        'views/resource.xml',
        'data/cron.xml',
    ],
}

