# -*- coding: utf-8 -*-
{
    'name': "Task Member Kanban",

    'summary': """
        Show all Assing users image in kanban.
        """,

    'description': """
        Added new tab Assing to in task in the project task
    """,

    'author': "Hashmicro / Kkumar - Vasant",
    'website': "http://www.hashmicro.com",

    'category': 'Project',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['project', 'project_extension'],

    # always loaded
    'data': [
        'views/project_task_view.xml'
    ],
}
