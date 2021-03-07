# -*- coding: utf-8 -*-
{
    "name": "POS Synchronization",
    "author": "HashMicro/ Amit Patel",
    "version": "1.1.1",
    "website": "www.hashmicro.com",
    "category": "Point Of Sale",
    'summary': 'POS Synchronization',
    'description': """
    	This module cover the following points:

        * Create default auditlog rule for customer,product template and product variants.		
        * Add pos_sync_id field in customer,product,product category,pos product category,payment method and it shold be the combination of the Branch ID + POS + Record ID
        * Sync customer,product,product category,pos product category and payment method using pos_sync_id and auditlogs.
        * Configuration for the POS Sync 
        * Add Logs for Customer,Product,Product Category, POS Product Category,Payment Method with the date and status[Success Or Failed]
* Sync the customer,product,product category,pos product category,payment method from the manual sycn using pos configuration and pos_sync_id
    """,
    "depends": [
        "branch",
        "branch_company",
        "auditlog",
        "product",
        "account",
        "point_of_sale",
        "pos_promotion",
        "full_pos_promotion",
        "pos_loyalty",
        "pos_loyalty_fix",
        "vouchers_pos",
        "voucher_gift_pos",
        "product_brand",
        "pos_multiple_category"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/auditlog_rule_data.xml",
        "views/res_partner_view.xml",
        "views/res_company_view.xml",
        "views/product_view.xml",
        "views/account_journal_view.xml",
        "views/sync_log_view.xml",
        "views/pos_order_view.xml",
        "views/pos_promotion_view.xml",
        "views/loyalty_view.xml",
        "views/pos_voucher_coupon_view.xml",
        "views/domain.xml",
        "wizard/product_sync_view.xml",
        "wizard/customer_sync_view.xml",
        "wizard/product_categ_sync_view.xml",
        "wizard/posproduct_categ_sync_view.xml",
        "wizard/payment_method_sync_view.xml",
        "wizard/promotion_sync_view.xml",
        "wizard/loyalty_sync_view.xml",
        "wizard/voucher_sync_view.xml",
        "wizard/coupon_sync_view.xml",
        "wizard/product_brand_sync_view.xml",
        "data/ir_config_parameter_data.xml",
        "wizard/pos_sync_config_view.xml",
    ],
    'demo': [],
    "installable": True,
    "auto_install": False,
    "application": True,
}
