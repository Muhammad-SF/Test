# -*- coding: utf-8 -*-
{
    # Module Info.
    'name': "std_timesheet_access_rights",
    'category': 'Uncategorized',
    'version': '1.1.1',
    'summary': """Timesheet Access Rights, Manage Timesheet Access,
    Timesheet Team, Role of user in timesheet.""",
    'description': """Timesheet Access Rights, Manage Timesheet Access,
    Timesheet Team, Role of user in timesheet.""",

    # Author
    'author': "Hashmicro/Techultra/Nikesh",
    'website': "http://www.hashmicro.com",

    # Dependencies
    'depends': ['hr', 'hr_timesheet', 'hr_timesheet_sheet', 'hr_timesheet_attendance',
                'project_timesheet_extension'],

    # Views
    'data': [
        'security/analytic_line_security.xml',
        'security/timesheet_team_security.xml',
        'security/ir.model.access.csv',
        'views/timesheet_team_view.xml',
    ],

    # Technical Specification
    'installable': True,
    'auto_install': False,
    'application': False,
}