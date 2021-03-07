    # -*- coding: utf-8 -*-

{
    'name': 'Coupons & Vouchers in POS ',
    #voucher_gift_pos
    'version': '1.1.4',
    'category': 'Point of Sale',
    'summary': 'Manage POS Vouchers Min Order Value for Coupon Codes & auto generate coupon based on order',
    'description':""" 
        - 170120 | 02- gift voucher - revision 7.docx: make scheduler for remind to customer when loyalty point will expired.
        - 280120 | Fixed. About access rights(Gift Voucher) according to that create gift voucher and generate coupons. | v1.2.
        - 030220 | Done issue, Only Manager can see "Approve" button. After approved by Manager. User, Admin and Manager can see "Generate Coupon" button.
            """,
    'author': "Hashmicro/ YYA-PYVTech /Krutarth-Techultra",
    'website': "http://www.hashmicro.com",
    'depends': ['vouchers_pos', 'product_brand','pos_loyalty_fix','branch','pos_loyalty'],
    'data': [
        'security/security_view.xml',
        'wizard/coupon_generation_wizard_view.xml',
        'wizard/pos_coupon_generation.xml',
        'views/gift_voucher.xml',
        'views/pos_template.xml',
        'views/pos_setting.xml',
        'views/limit_membership.xml',
        # 'views/pos_promotion_view.xml'
        
            ],
    'qweb': [
            'static/src/xml/pos.xml',
            'static/src/xml/custom_button.xml',
    ],
    # 'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
