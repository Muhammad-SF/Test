# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang

import odoo.addons.decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).

        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        invoice_line = self.env['account.invoice.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                product_id = vals.get('product_id')
                inv_line_rec = invoice_line.search([('invoice_id','=',invoice_id),('product_id','=',product_id)]) or []
                if not inv_line_rec:
                	invoice_line.create(vals)
                for inv_line in inv_line_rec:
                    if product_id not in [inv_line.product_id.id]:
                        invoice_line.create(vals)
                    else:
                        qty = inv_line.quantity + vals.get('quantity',0.0)
                        vals.update({'quantity': qty})
                        inv_line.write(vals)
