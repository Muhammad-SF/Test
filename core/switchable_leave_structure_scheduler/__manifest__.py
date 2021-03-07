# -*- coding: utf-8 -*-
{
    'name': 'Switchable Leave Structure Scheduler',
    'summary': 'Switchable leave structure for the employees',
    'description': 'Switchable leave structure for the employees according to time of service',
    'version': '1.1.1',
    'category': 'Human Resources',
    'author': 'HashMicro / Kartikeya Gupta',
    'depends': ['sg_holiday_extended','leave_allocate_years_of_service_interval'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/leave_structure.xml',
        'data/structure_related_schedular.xml',
        # 'wizard/renew_contract.xml'
    ],
    'application': True,
    'installable': True,
}
