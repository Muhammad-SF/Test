# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    def show_stock(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock balance by location',
            'res_model': 'product.product',
            'res_id' : self.product_id.id,
            'view_id' : self.env.ref('rfq_check_stock.stock_by_product_form_view1').id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }

