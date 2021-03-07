# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class sh_stock_picking(models.Model):
    _inherit = 'stock.picking'


class sh_stock_move(models.Model):
    _inherit = "stock.move"
    
    sh_sec_qty = fields.Float("Secondary Qty", digits=dp.get_precision('Product Unit of Measure'))
    sh_sec_uom = fields.Many2one("product.uom", 'Secondary UOM')

    @api.model
    def create(self, vals):
        res = super(sh_stock_move, self).create(vals)
        if res.procurement_id.sale_line_id and res.procurement_id.sale_line_id.sh_is_secondary_unit == True and res.procurement_id.sale_line_id.sh_sec_uom:
            res.update({'sh_sec_uom':res.procurement_id.sale_line_id.sh_sec_uom.id, 'sh_sec_qty':res.procurement_id.sale_line_id.sh_sec_qty})
        elif res.purchase_line_id and res.purchase_line_id.sh_is_secondary_unit == True and res.purchase_line_id.sh_sec_uom:
            res.update({'sh_sec_uom':res.purchase_line_id.sh_sec_uom.id, 'sh_sec_qty':res.purchase_line_id.sh_sec_qty})
        return res

    
class sh_stock_pack_operation_link(models.Model):
    _inherit = 'stock.move.operation.link'
    
    @api.model
    def create(self, vals):
        res = super(sh_stock_pack_operation_link, self).create(vals)
        res.operation_id.update({
            'sh_sec_qty':res.move_id.sh_sec_qty,
            'sh_sec_uom':res.move_id.sh_sec_uom.id,
            })
        return res


class sh_stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"
     
    sh_sec_qty = fields.Float("Secondary Qty", digits=dp.get_precision('Product Unit of Measure'))
    sh_sec_done_qty = fields.Float("Secondary Done Qty", digits=dp.get_precision('Product Unit of Measure'), store=True)
    sh_sec_uom = fields.Many2one("product.uom", 'Secondary UOM')
    sh_is_secondary_unit = fields.Boolean("Related Sec Uni", related="product_id.sh_is_secondary_unit")

    @api.onchange('qty_done')
    def onchange_product_uom_done_qty_sh(self):
        if self and self.sh_is_secondary_unit == True and self.sh_sec_uom:
            self.sh_sec_done_qty = self.product_uom_id._compute_quantity(self.qty_done, self.sh_sec_uom)
 
    @api.onchange('sh_sec_done_qty')
    def onchange_sh_sec_done_qty_sh(self):
        if self and self.sh_is_secondary_unit == True and self.product_uom_id:
            self.qty_done = self.sh_sec_uom._compute_quantity(self.sh_sec_done_qty, self.product_uom_id)
             
             
