{
      'name' : 'Work Order Lines Report',  
      'version' : '1.1.1',
      'author' : 'Hash Micro',
      'category' : 'Account Contract',
      'depends' : ['manufacturing_material_consumption','work_order_expansion'],
    'description' : """

              Work Order Lines Report.
                    
                    """,
    "website" : "Hash Micro",
    "data" : [
             'views/work_order_inherit_view.xml',
             ],
    'css': [

    ],
    'qweb': [
            'static/src/xml/template.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
   
}
