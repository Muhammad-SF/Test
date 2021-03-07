# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        is_user_rate_so = self.env['ir.values'].sudo().get_default('sale.config.settings', 'is_user_rate_so')
        if is_user_rate_so == True:
            if order.rate_type:
                res.rate_type = order.rate_type
            if order.rate_type == 'c1':
                res.c1_rate = order.c1_rate
            else:
                res.u1_rate = order.u1_rate
            if order.currency_id:
                res.currency_id = order.currency_id.id
        return res

SaleAdvancePaymentInv()