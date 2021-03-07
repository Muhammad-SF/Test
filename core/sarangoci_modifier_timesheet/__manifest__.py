# -*- coding: utf-8 -*-
{
    'name': "Sarangoci Modifier Timesheet",

    'description': """
        Timesheet
    """,
    'author': 'HashMicro / Quy',
    'website': 'www.hashmicro.com',

    'category': 'timesheet',
    'version': '1.1.1',

    'depends': ['hr_timesheet_sheet','hr_timesheet_attendance'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/employee_sequence.xml',
        'views/timesheet_view.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],
    'demo': [
    ],
}