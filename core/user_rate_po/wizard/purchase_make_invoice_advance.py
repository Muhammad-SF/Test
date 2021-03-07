# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PurchaseAdvancePaymentInv(models.TransientModel):
    _inherit = "purchase.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, po_line, amount):
        res = super(PurchaseAdvancePaymentInv, self)._create_invoice(order, po_line, amount)
        is_user_rate_po = self.env['ir.values'].sudo().get_default('purchase.config.settings', 'is_user_rate_po')
        if is_user_rate_po == True:
            if order.rate_type:
                res.rate_type = order.rate_type
            if order.rate_type == 'c1':
                res.c1_rate = order.c1_rate
            else:
                res.u1_rate = order.u1_rate
            if order.currency_id:
                res.currency_id = order.currency_id.id
        return res

PurchaseAdvancePaymentInv()
