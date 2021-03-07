{
    'name': 'Sales Executive',
    'description': 'This module will modify Sales Executive Rules.',
    'category': 'SALE',
    'version': '1.1.1',
    'author': 'HashMicro / MP Technolabs',
    'website': 'www.hashmicro.com',
    'depends': ['crm','sales_team','helpdesk'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'application': True,
    'installable': True,
}