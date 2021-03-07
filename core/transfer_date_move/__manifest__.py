{
    'name': 'Stock Transfer Back Date Move',
    'version': '1.1.3',
    'sequence': 1,
    'category': 'Stock',
    'summary': 'Stock transfer back date base on schedule date. It will help to put back date PO/ SO transaction that use multi currency. Rate usage and JE date will be base on the chosen Schedule Date on the picking.',
    'description': """
        Stock transfer back date base on schedule date. It will help to put back date PO/ SO transaction that use multi currency. Rate usage and JE date will be base on the chosen Schedule Date on the picking.
    """,
    'author': 'Hashmicro / Allen',
    'website': 'https://www.hashmicro.com/',
    'depends': ['stock','stock_account','full_inv_adjustment_branch'],
    'data': [
        'views/stock_move.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
