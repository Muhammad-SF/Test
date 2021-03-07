# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
	_inherit = "res.partner"

	@api.multi
	def action_view_vendor_po_shipment(self):
		
		action = self.env.ref('stock.action_picking_tree_all').read()[0]
		stock_obj = self.env['stock.picking']
		partner_ids= stock_obj.search([('partner_id','=',self.name),('picking_type_id.code','=','outgoing')])
		supplier_ids= stock_obj.search([('partner_id','=',self.name),('picking_type_id.code','=','incoming')])

		if self._context.get('search_default_customer') == 1:
			action['domain']=[('id','in' , partner_ids.ids)]

		if self._context.get('search_default_supplier') == 1:
			action['domain']=[('id','in' , supplier_ids.ids)]
			
		return action