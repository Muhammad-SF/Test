# -*- coding: utf-8 -*-
{
    'name': "Salesperson Meetings Leads Analysis",
    'version': "1.1.1",
    'author': "Hashmicro/Antsyz-Kannan",
    'license': "AGPL-3",
    'summary': 'setup to create excel reports for salesperson.',
    'description': "This module includes creation of excel reports for salesperson to get no. of leads and its related meetings within given period.",
    'website': "http://www.hashmicro.com",
    'category': "crm",
    'depends': [
        'crm',
    ],
    'data': [
        'wizard/salesperson_analysis_wizard_view.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
