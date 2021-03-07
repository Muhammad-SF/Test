# -*- coding: utf-8 -*-
{
    'name': "Sarangoci Actual Timesheet",

    'description': """
        Timesheet,Human Resources
    """,
    'author': 'HashMicro / Quy/ MP Technolabs - Purvi',
    'website': 'www.hashmicro.com',

    'category': 'timesheet',
    'version': '1.1.1',

    'depends': ['hr_timesheet_sheet','hr_timesheet_attendance','sarangoci_forecast_timesheet'],

    # always loaded
    'data': [
        'views/hr_timesheet_sheet.xml',
    ],
    # only loaded in demonstration mode
    'qweb': ['static/src/xml/timesheet.xml',],
    'demo': [],
}