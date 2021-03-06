# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'School',
    'version': '1.1.1',
    'author': '''Serpent Consulting Services Pvt. Ltd.''',
    'website': 'http://www.serpentcs.com',
    'images': ['static/description/school.png'],
    'category': 'School Management',
    'license': "AGPL-3",
    'complexity': 'easy',
    'Summary': 'A Module For School Management',
    'depends': ['hr', 'crm', 'report'],
    'data': ['security/school_security.xml',
             'security/ir.model.access.csv',
             'wizard/terminate_reason_view.xml',
             'wizard/wiz_send_email_view.xml',
             'views/school_view.xml',
             'data/student_sequence.xml',
             'wizard/assign_roll_no_wizard.xml',
             'wizard/move_standards_view.xml',
             'views/report_view.xml',
             'views/identity_card.xml'],
    'demo': [],# 'demo/school_demo.xml'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True
}
