{
    'name': "Warehouse Stock Restrictions Extended",
    'summary': """
         Warehouse and Stock Location Restriction on Users.""",
    'description': """
        This Module Restricts the User from Accessing Warehouse and Process Stock Moves other than allowed to Warehouses and Stock Locations.
    """,
    'author': "HashMicro / Prince",
    'category': 'Warehouse',
    'version': '1.1.2',
    'depends': ['stock','warehouse_stock_restrictions','user_super_admin_access'],
    'data': [
        'security/ir.model.access.csv', 
        'views/res_users_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}