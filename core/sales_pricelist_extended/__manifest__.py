{
    'name':'Sales Pricelist Extended',
    'depends': ['base','sale','branch','sales_team','product'],
    'description': """Approving Matrix Pricelist""",
    'website' : 'Hashmicro ',
    'version': '2.2.1',
    'author': 'Hashmicro',
    
    'data': [
           'security/ir.model.access.csv',
           'views/pricelist_view.xml',
            'views/sale_order_view.xml',
             ],

    'installable': True,
    'application': True,
    'auto_install': False,

}
