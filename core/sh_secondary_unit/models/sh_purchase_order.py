# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class sh_purchase_order_line(models.Model):
    _inherit = "purchase.order.line"
    
    sh_sec_qty = fields.Float("Secondary Qty", digits=dp.get_precision('Product Unit of Measure'))
    sh_sec_uom = fields.Many2one("product.uom", 'Secondary UOM')
    sh_is_secondary_unit = fields.Boolean("Related Sec Uni", related="product_id.sh_is_secondary_unit")
    category_id = fields.Many2one("product.uom.categ", "Category", related="product_uom.category_id")

    @api.onchange('product_qty', 'product_uom')
    def onchange_product_uom_qty_sh(self):
        if self and self.sh_is_secondary_unit == True and self.sh_sec_uom:
            self.sh_sec_qty = self.product_uom._compute_quantity(self.product_qty, self.sh_sec_uom)

    @api.onchange('sh_sec_qty', 'sh_sec_uom')
    def onchange_sh_sec_qty_sh(self):
        if self and self.sh_is_secondary_unit == True and self.product_uom:
            self.product_qty = self.sh_sec_uom._compute_quantity(self.sh_sec_qty, self.product_uom)

    @api.multi
    @api.onchange('product_id')
    def onchange_secondary_uom(self):
        if self:
            for rec in self:
                if rec.product_id.sh_is_secondary_unit == True and rec.product_id.uom_id:
                    rec.sh_sec_uom = rec.product_id.sh_secondary_uom.id
                elif rec.product_id.sh_is_secondary_unit == False:
                    rec.sh_sec_uom = False
                    rec.sh_sec_qty = 0.0
