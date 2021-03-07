# -*- coding: utf-8 -*-
{
    'name': 'Salary Bonus Deduction',
    'version': '1.1.1',
    'category': 'Human Resources',
    'sequence': 12,
    'summary': 'setup for bonus and deduction in payslip',
    'description': "This module includes setup for bonus and deduction in payslip of employee.",
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Kannan',
    'depends': [
        'l10n_sg_hr_payroll'
    ],
    'data': [
        'views/payroll_extended_view.xml',
        'data/hr_salary_rule.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}