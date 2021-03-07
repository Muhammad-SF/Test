# -*- coding: utf-8 -*-
# Copyright 2017-2018 ZAD solutions (<http://www.zadsolutions.com>).
#  License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# 'author': 'umar_3ziz@hotmail.com',

{
    'name': 'Tasks Timer',
    'category': 'project',
    "version": "1.1.1",
    'author': 'Omar Abdulaziz',
    'description': """
Enhancement of the module Project to add Timer for every task and user can add his Timesheet easily 
==========================
    """,
    'website': 'https://www.zadsolutions.com',
    'depends': ['project', 'hr_timesheet'],
    'data': [
        'views/project_tasks_chanegs_view.xml',
        'views/project_timesheets_work_view.xml',

    ],
    'installable': True,
    'license': 'AGPL-3',
    'price': 10.00,
    'currency': 'EUR',
    'images': [
        'static/description/TimerCover.png',
    ],
}