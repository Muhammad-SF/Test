# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "All in one secondary unit of measure- Sales, Purchase, Accounting and Inventory",
    "version": "1.1.1",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "summary": "",
    "description": """
	Do you have more than one unit of measure in product ? Yes! so, you are at right palce. 
    	We have created beautiful module to manage secondary unit of product in sales, pruchase, inventory operations and accounting. 
    	It will help you to get easily secondary unit value. so you don't need to waste your time to calculate that value.
    	you can also show that value in pdf reports so your customer/vendor also easily understand that.
    	
    sales secondary uom 
    sales secondary unit of measure
    sale order secondary uom 
    sale order secondary unit of measure
    purchase secondary uom 
    purchase secondary unit of measure
    purchase order secondary uom 
    purchase order secondary unit of measure
    inventory secondary uom 
    stock unit of measure
    delivery incoming order secondary uom 
    delivery incoming order secondary unit of measure
    invoice secondary unit
    bill secondary unit
    invoice secondary unit of measure
    invoice secondary uom    
    bill secondary unit of measure
    bill secondary uom    	
                    """,
    "version":"1.1.1",
    "depends" : [
                    "sale",
                    "account_accountant",
                    "purchase",
                    "stock",
                ],
    "application" : True,
    "data" : [
            "security/secondary_unit_group.xml",
            "views/sh_product_template_custom.xml",
            "views/sh_product_custom_view.xml",
            "views/sh_sale_order_view.xml",
            "views/sh_purchase_order_view.xml",
            "views/sh_account_invoice_view.xml",
            "views/sh_stock_picking_view.xml",
            "views/sh_stock_pack_operation_lot_form_view.xml",
            "views/sh_stock_scrap_view.xml",
            "report/sh_report_sale_order.xml",
            "report/sh_report_purchase_order.xml",
            "report/sh_report_account_invoice.xml",
	    "report/sh_stock_reports_view.xml",
            ],
    "auto_install":False,
    "installable" : True,
    "price": 40,
    "currency": "EUR",
    "images": ['static/description/background.png', ],
}







