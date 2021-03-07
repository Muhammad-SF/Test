# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class sh_stock_pack_operation_lot(models.Model):
    _inherit = 'stock.pack.operation.lot'
    
    sh_sec_done_qty = fields.Float("Secondary Done Qty", digits=dp.get_precision('Product Unit of Measure'), store=True)
    
    @api.onchange('qty')
    def onchange_stock_pack_done_qty_sh(self):
        if self and self.operation_id.sh_is_secondary_unit == True and self.operation_id.sh_sec_uom:
            self.sh_sec_done_qty = self.operation_id.product_uom_id._compute_quantity(self.qty, self.operation_id.sh_sec_uom)
 
    @api.onchange('sh_sec_done_qty')
    def onchange_sh_sec_stock_done_qty_sh(self):
        if self and self.operation_id.sh_is_secondary_unit == True and self.operation_id.product_uom_id:
            self.qty = self.operation_id.sh_sec_uom._compute_quantity(self.sh_sec_done_qty, self.operation_id.product_uom_id)
