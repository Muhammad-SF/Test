# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _


class sh_product_product(models.Model):
    _inherit = 'product.product'

    category_id = fields.Many2one("product.uom.categ", "Category", related="uom_id.category_id")


class sh_product_template(models.Model):
    _inherit = 'product.template'
    
    sh_secondary_uom = fields.Many2one('product.uom', 'Secondary UOM')
    sh_secondary_uom_onhand = fields.Float('On Hand', compute='get_secondary_unit_on_hand_qty')
    sh_secondary_uom_forecasted = fields.Float('Forecasted', compute='get_secondary_unit_forecasted_qty')
    sh_uom_name = fields.Char("Secondary UOM", related='sh_secondary_uom.name', readonly=True)
    sh_is_secondary_unit = fields.Boolean("is Secondary Unit ?")
    category_id = fields.Many2one("product.uom.categ", "Category", related="uom_id.category_id")

    @api.multi
    def get_secondary_unit_on_hand_qty(self):
        if self:
            for rec in self:
                if rec.sh_secondary_uom:
                    rec.sh_secondary_uom_onhand = rec.uom_id._compute_quantity(rec.qty_available, rec.sh_secondary_uom)
    
    @api.multi
    def get_secondary_unit_forecasted_qty(self):
        if self:
            for rec in self:
                if rec.sh_secondary_uom:
                    rec.sh_secondary_uom_forecasted = rec.uom_id._compute_quantity(rec.virtual_available, rec.sh_secondary_uom)
    
    @api.multi
    def action_open_sh_quants(self):
        products = self.mapped('product_variant_ids')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_locationgroup': 1, 'search_default_internal_loc': 1}
        return action


class sh_stock_quant(models.Model):
    _inherit = 'stock.quant'
    
    sh_secondary_unit_qty = fields.Float('On Hand', related="product_id.sh_secondary_uom_onhand")
    sh_secondary_unit = fields.Many2one('product.uom', 'Secondary UOM', related='product_id.sh_secondary_uom')
