# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    @api.multi
    def action_confirm(self):
    	res = super(SaleOrder, self.with_context({'sale_do': 1})).action_confirm()
    	return res
    	
class stock(models.Model):
	_inherit = "stock.picking"
	
	@api.model
	def create(self, vals):
		res = super(stock, self).create(vals)
		sp_types = self.env['stock.picking.type'].search([('code', '=', 'incoming')])
		for rec in sp_types:
			if self._context.get('sale_do'):
				res.picking_type_id = rec
			return res
