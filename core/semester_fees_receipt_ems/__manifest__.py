# -*- coding: utf-8 -*-
{
    "name": "Student Semester Fees",
    "author": "HashMicro/ Amit Patel",
    "version": "1.1.1",
    'description': '''
    	1/ This module help to create a semester(Configured No Of Months) fees receipt for the Student.
    ''',
    'summary': 'Student Semester Fees',
    "website": "www.hashmicro.com",
    "category": "School Management",
    "depends": ['school','school_fees','fees_receipt_ems'],
    "data": [
		'views/student_fees_view.xml',
		'data/cron.xml',
    ],
    "qweb": [],
    'demo': ['data/school_fees_demo.xml'],
    'installable': True,
    'auto_install': False,
}
