# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = "stock.move"

    category_id = fields.Many2one('product.category',string='Product Category',related='product_id.categ_id',store=True)