# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import models, fields, api

class CommissionSchemeProductCategory(models.Model):
    _name = 'commission.scheme.productcategory'
    _description = 'Commission Scheme Product Category'

    commission_scheme_id = fields.Many2one(comodel_name='commission.scheme', string='Commission Scheme ID')
    target = fields.Float(string='Min Sales')
    max_sales = fields.Float(string='Max Sales')
    product_category_id = fields.Many2one(comodel_name='product.category', string='Product Category')
    commission_amount = fields.Float(string='Commission Amount')
    percent_of_sales = fields.Float(string='% of Sales')
    reached = fields.Float(string='Reached', default=0.0)
    to_target = fields.Float(string='To Achieve Target', compute='_compute_to_target')

    @api.multi
    def _compute_to_target(self):
        for rec in self:
            rec.to_target = rec.target - rec.reached