# -*- coding: utf-8 -*-
{
    'name': 'Scholarship Management',
    'summary': 'Allow users to record Scholarships available and for Students to apply for Scholarship',
    'description': 'Scholarship management : Allow users to record scholarships and allow students to avail scholarships',
    'version': '1.1.1',
    'category': 'Student',
    'author': 'Hashmicro/Saravanakumar',
    'website': 'www.hashmicro.com',
    'depends': ['school'],
    'data': [
        'security/ir.model.access.csv',
        'views/scholarship_view.xml',
    ],
    'application': True,
}