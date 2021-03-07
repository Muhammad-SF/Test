# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.addons import decimal_precision as dp

class ProductCategory(models.Model):
    _inherit = 'product.category'

    variance_account = fields.Many2one('account.account', 'Variance Account', company_dependent=True,
        domain=[('deprecated', '=', False)])

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    variance_account = fields.Many2one('account.account', 'Variance Account', company_dependent=True,
        domain=[('deprecated', '=', False)])

class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        # calculated purchase change the journal items structure.
        partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
        variance_amount = 0.0
        positive_variance = False
        negative_variance = False
        variant_account = self.product_id.variance_account or self.product_id.categ_id.variance_account
        if self.picking_type_id.code == 'incoming' and self.product_id.cost_method == 'standard' and variant_account:
            if self.product_id.standard_price < self.purchase_line_id.price_unit:
                positive_variance = True
                variance_amount = abs(self.purchase_line_id.price_unit - self.product_id.standard_price)
                var_debit_line_vals = {
                    'name': self.name,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'ref': self.picking_id.name,
                    'partner_id': partner_id,
                    'debit': variance_amount,
                    'credit': 0,
                    'account_id': variant_account.id,
                }
                res.append((0, 0, var_debit_line_vals))
            if self.product_id.standard_price > self.purchase_line_id.price_unit:
                negative_variance = True
                variance_amount = abs(self.product_id.standard_price - self.purchase_line_id.price_unit)
                var_credit_line_vals = {
                    'name': self.name,
                    'product_id': self.product_id.id,
                    'quantity': qty,
                    'product_uom_id': self.product_id.uom_id.id,
                    'ref': self.picking_id.name,
                    'partner_id': partner_id,
                    'credit': variance_amount,
                    'debit': 0,
                    'account_id': variant_account.id,
                }
                res.append((0, 0, var_credit_line_vals))

        for num in range(0, 2):
            if res and res[num] and res[num][2] and res[num][2]["credit"]:
                if positive_variance:
                    res[num][2].update({'credit': res[num][2]["credit"] + variance_amount })
                if negative_variance:
                    res[num][2].update({'credit': res[num][2]["credit"] - variance_amount })
        return res