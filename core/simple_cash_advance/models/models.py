# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    is_advance = fields.Boolean('Is Advance')
    is_product = fields.Boolean('Is Product')
    product = fields.Char('Product', compute = '_compute_product', store=True)
    product_id = fields.Many2one('product.product', string='Product', store=True, domain=[('can_be_expensed', '=', True)], required=True)
    
    @api.onchange('unit_amount')
    def onchange_unit_amount(self):
        if self.is_advance:
            self.unit_amount = -(abs(self.unit_amount))

    @api.one
    @api.depends('is_advance')
    def _compute_product(self):
        if self.is_advance:
            self.product = self.env.ref('simple_cash_advance.cash_product').name
            self.product_id = self.env.ref('simple_cash_advance.cash_product').id

            

