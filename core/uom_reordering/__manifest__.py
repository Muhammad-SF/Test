# -*- coding: utf-8 -*-
{
    'name': "UOM Reordering",
    # nri_pos_reference_branch

    'summary': """
        Unit of Measures on Reordering Rules        
        """,

    'description': """
        Module Name: uom_reordering
        Is an Existing Module: ☐ (If checked, then edit the module, if unchecked, create new module)
        Dependency: stock

        **NOTE: Please copy the Module Details below to the module’s actual description so it can be viewed in Apps**
        Module Details: Add Unit Of Measure field
        1)Menu Item Inventory &gt; Inventory Control &gt; Reordering Rules
        New / Existing
        Object

        New / Existing
        Menu Item

        Access Rights to New
        Object / Menu Item

        Form View Fields
        (Add / Edit / Hide / Remove)

        Existing Existing Use the default access for
        Reordering Rules

        Add:
        - Unit of Measures: Dropdown autofill by
        object product.product field uom_po_id
        based on the Product that chosen in object
        stock.warehouse.orderpoint field
        product_id (Editable). Put this field below
        object stock.warehouse.orderpoint field
        product_id.

        Remove:
        - object stock.warehouse.orderpoint field
        product_uom
    """,

    'author': "HashMicro/Semir Worku",
    'website': "http://www.hashmicro.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Warehouse',
    'version': '1.1.1',

    # any module necessary for this one to work correctly
    'depends': ['stock','product'],

    # always loaded
    'data': [
        'views/stock_warehouse_orderpoint.xml',
    ],
}