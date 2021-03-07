# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    group_receipt_supplier_matrix = fields.Boolean("Use for receipt/supplier approving matrix menu", implied_group='sg_partner_payment.group_receipt_supplier_matrix',
                                       help="""Allows to show Receipt/Supplier Approving Matrix menu. """)
    group_supplier_matrix = fields.Boolean("Use for supplier approving matrix menu",
                                                   implied_group='sg_partner_payment.group_supplier_matrix',
                                                   help="""Allows to show Supplier Approving Matrix menu. """)

    @api.onchange('is_customer_receipt_approving_matrix', 'is_supplier_payment_approving_matrix')
    def onchange_receipt_supplier_matrix(self):
        if self.is_customer_receipt_approving_matrix:
            self.group_receipt_supplier_matrix = True
        else:
            self.group_receipt_supplier_matrix = False

        if self.is_supplier_payment_approving_matrix:
            self.group_supplier_matrix = True
        else:
            self.group_supplier_matrix = False

AccountConfigSettings()