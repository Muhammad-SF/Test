# -*- coding: utf-8 -*-
{
    'name': 'Reordering Rule Extended Core',
    'version': '1.2.3',
    'category': 'Inventory',
    'sequence': 17,
    'summary': 'Reordering Rules',
    'description': """Reordering Rules could set by period of time for each product. There could be different rules by the period.
                """,
    'website': 'http://www.hashmicro.com/',
    'author': 'Hashmicro/Shivam DUdhat (Laxicon Solution)/Kinjal/SetuConsulting/Updadhyay',
    'depends': [
        'std_material_request', 'mail', 'approving_matrix_pr', 'internal_transfer_receipt'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduler_re-order.xml',
        'data/reordering_mail.xml',
        'views/reorder_rule_view_extend.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
