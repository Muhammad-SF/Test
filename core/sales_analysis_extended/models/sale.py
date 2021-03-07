# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # invoice_numbers_ext = fields.Char(compute='_compute_test_f1', string='Invoices', copy=False, store=True)
    invoice_numbers_ext = fields.Char(compute='_compute_test_f1', string='Invoices', store=True)
    sale_invoice_numbers = fields.Char(compute='_compute_test_f1', string='Invoices', store=True)
    test_f1 = fields.Boolean(string='Can Edit Delivered', readonly=True, default=True) 

    @api.multi
    @api.depends('invoice_ids')
    def _compute_test_f1(self):
        for order in self:
            inv_numbers = []
            if order.invoice_ids:
                for invoice in order.invoice_ids:
                    if invoice.state in ['open', 'paid']:
                        inv_numbers.append(invoice.number)
                str1 = ""
                if inv_numbers:
                    str1 = ','.join(inv_numbers)
                if str1:
                    order.invoice_numbers_ext = str1
                    order.sale_invoice_numbers = str1
                    #abc = order.write({'invoice_numbers_ext': str1}) 
        return True   
    
# class SaleReport(models.Model):
#     _inherit = "sale.report"
#
#     invoice_numbers_ext = fields.Char(string='Invoices', readonly=True)
#
#     def _select(self):
#         return super(SaleReport, self)._select() + ", s.invoice_numbers_ext as invoice_numbers_ext"
#
#     def _group_by(self):
#         return super(SaleReport, self)._group_by() + ", s.invoice_numbers_ext"
