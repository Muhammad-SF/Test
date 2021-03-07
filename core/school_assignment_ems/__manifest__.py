# -*- coding: utf-8 -*-

{
    'name': 'Student Assignment',
    'version': '1.1.1',
    'summary': 'Student Assignment',
    'description': """
        This module help to assign a assignment work to the student and based on that submited work , faculty will give the grade and rank to that student.
    """,
    'author': 'HashMicro / Amit Patel',
    'website': 'www.hashmicro.com',
    'category': 'School Management',
    'sequence': 0,
    'images': [],
    'depends': ['school'],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',
        'views/assignment_view.xml',
        'menu.xml',
        'sequence.xml'
        ],
    'installable': True,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
