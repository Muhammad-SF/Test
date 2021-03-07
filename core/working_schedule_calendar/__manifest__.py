# -*- coding: utf-8 -*-
{
    'name': "Employee Working Schedule Calendar",

    'description': """
        
        1. Develop calendar view based on employee's calendar working schedule
        
        2. Enhance the working schedule to have "Alternate Week" function. For example, employees work on 1st and 3rd Saturday every month.
        
        3. Develop the working schedule for shift pattern.

    """,

    'author': 'HashMicro / Dev (Braincrew Apps)/ Paras',
    'website': 'https://www.hashmicro.com',
    
    'category': 'Uncategorized',
    'version': '1.1.6',

    # any module necessary for this one to work correctly
    'depends': [
        'hr_contract',
        'resource',
        'sg_holiday_extended',
        'hr_attendance',
        'web_calendar',
        'hr_payroll',
        'web_calendar',
#         'working_schedule',
    ],

    # always loaded
     "qweb": [
        "static/src/xml/calendar_view.xml",
        # "static/src/xml/attendance.xml",
    ],

    'data': [
        'views/shift_pattern_view.xml',
        'views/resource.xml',
        'views/employee_working_schedule_view.xml',
        'views/shift_daily_view.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',
    ],

    # only loaded in demonstration mode
    'demo': [],
}

