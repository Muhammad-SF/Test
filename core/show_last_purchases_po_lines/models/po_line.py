# -*- coding: utf-8 -*-

from odoo import models, fields, api

class show_last_purchases_po_lines(models.Model):
    _name = 'custom.p.line'

    purchase_line_id = fields.Many2one('purchase.order.line','Purchase')
    vendor_id = fields.Many2one('res.partner',string="Vendor")
    product_id = fields.Many2one('product.product',string="Product")
    qty = fields.Float("Quantity")
    price = fields.Float("Price")
    date = fields.Datetime("Date")

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order.line'
    
    p_line_ids = fields.One2many('custom.p.line','purchase_line_id', string="Po Line")

    @api.onchange('product_id')
    def onchange_name(self):
        if self.product_id:
            purchase_line_ids = self.env['purchase.order.line'].search([('product_id','=',self.product_id.id)])
            
            line_list = []
            if purchase_line_ids:
                for line in purchase_line_ids:
                    if line.order_id.state == 'purchase':
                        line_list.append((0,0,{'vendor_id':line.order_id.partner_id.id,
                                                'product_id':line.product_id.id,
                                                'qty':line.product_qty,
                                                'price':line.price_subtotal,
                                                'date':line.date_planned}))
            
            self.p_line_ids = line_list