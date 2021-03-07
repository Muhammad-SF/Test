# -*- coding: utf-8 -*-

from odoo import models, fields, api

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account')

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        result = super(sale_order_line, self).invoice_line_create(invoice_id, qty)
        for line in self:
            for invoice_line in line.invoice_lines:
                invoice_line.write({
                    'account_analytic_id': line.account_analytic_id.id
                })
        return result