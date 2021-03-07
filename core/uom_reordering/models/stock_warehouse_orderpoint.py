# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api


class Orderpoint(models.Model):
    """ Defines Minimum stock rules. """
    _inherit = "stock.warehouse.orderpoint"
    purchase_product_uom = fields.Many2one('product.uom', 'Purchase Unit of Measure',readonly=False,default=lambda self: self._context.get('product_uom', False))   

    @api.onchange('product_id')
    def on_product_change(self):
    	if self.product_id:
    		self.purchase_product_uom=self.product_id.uom_po_id.id 