# -*- coding: utf-8 -*-
import datetime
import math
from dateutil import relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, Warning,UserError

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    limit_receiving_quantity = fields.Boolean('Limit Receiving Quantity', store=True)
    limit_per = fields.Float('Limit %')


class StockPicking(models.Model):
    _inherit = 'stock.picking'
                    
    @api.multi
    @api.depends('state','pack_operation_product_ids.qty_done')
    def check_received_qty_limit(self):
        limit_value = []
        for rec in self:
            order_line = self.env['purchase.order'].search([('name','=',rec.origin),('partner_id','=',rec.partner_id.id)])
            for line in rec.pack_operation_product_ids:
                    ref = line.product_id.default_code
                    product_name = '[' + ref + ']' + ' ' + line.product_id.name if ref else line.product_id.name
                    for po in order_line.order_line:
                        if line.product_id.id == po.product_id.id and po.max_limit_received_qty:
                            limit_value.append({
                                'vendor_id' : rec.partner_id,
                                'vendor' : rec.partner_id.name,
                                'product' : product_name,
                                'product_qty' : po.product_qty,
                                'qty_done' : line.qty_done,
                                'limit_value' : po.max_limit_received_qty
                                })
            return limit_value
        
    
    @api.multi
    def do_new_transfer(self):
        limit_value=self.check_received_qty_limit()
        for rec in self:
            rcvd_qty_limit = ""
            count = 0
            for i in limit_value:
                count += 1
            for value in limit_value:
                if value.get('qty_done') > value.get('limit_value'):
                    product = value.get('product')
                    rcvd_qty_limit += (product + ', ') if count > 1 else product
            if rcvd_qty_limit:
                raise UserError(_('You have reached the limit of receiving quantity for %s of %s' %(rec.partner_id.name,rcvd_qty_limit)))
        return super(StockPicking, self).do_new_transfer()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    max_limit_received_qty = fields.Integer('Max. Limit Receiving Quantity',compute="calculate_max_limit_received_qty")
    max_limit = fields.Float('Received Quantity',compute="calculate_max_limit")
    
    @api.multi
    @api.depends('qty_received')
    def calculate_max_limit(self):
        for rec in self:
            vendor_pricelist_obj = self.env['product.supplierinfo'].search([('name','=',rec.order_id.partner_id.id),('product_tmpl_id','=',rec.product_id.id),('limit_receiving_quantity','=',True)])
            max_min_qty = [min_qty.min_qty if rec.product_qty >= min_qty.min_qty else False for min_qty in vendor_pricelist_obj]
            min_min_qty = [min_qty.min_qty if rec.product_qty <= min_qty.min_qty else False for min_qty in vendor_pricelist_obj]
            if max_min_qty:
                min_qty = float(max(max_min_qty))
                if rec.product_qty >= min_qty:
                    limit_per = self.env['product.supplierinfo'].search([('name','=',rec.order_id.partner_id.id),('product_tmpl_id','=',rec.product_id.id),('limit_receiving_quantity','=',True),('min_qty','=',min_qty)])
                    limit = round(((rec.product_qty * limit_per.limit_per) / 100) + rec.product_qty)
                    rec.max_limit = limit
            if min_min_qty:
                min_qty1 = float(min(min_min_qty))
                if rec.product_qty <= min_qty1:
                    limit_per1 = self.env['product.supplierinfo'].search([('name','=',rec.order_id.partner_id.id),('product_tmpl_id','=',rec.product_id.id),('limit_receiving_quantity','=',True),('min_qty','=',min_qty1)])
                    limit1 = round(((rec.product_qty * limit_per1.limit_per) / 100) + rec.product_qty)
                    rec.max_limit = limit1
                
    
    @api.multi
    @api.depends('qty_received','product_qty')
    def calculate_max_limit_received_qty(self):
        for rec in self:
            vendor_pricelist_obj = self.env['product.supplierinfo'].search([('name','=',rec.order_id.partner_id.id),('product_tmpl_id','=',rec.product_id.id),('limit_receiving_quantity','=',True)])
            #first check that received any qty or not in PO lines
            if not rec.qty_received:
                max_min_qty = [min_qty.min_qty if rec.product_qty >= min_qty.min_qty else False for min_qty in vendor_pricelist_obj]
                min_min_qty = [min_qty.min_qty if rec.product_qty <= min_qty.min_qty else False for min_qty in vendor_pricelist_obj]
                if max_min_qty:
                    min_qty = float(max(max_min_qty))
                    if rec.product_qty >= min_qty:
                        limit_per = self.env['product.supplierinfo'].search([('name','=',rec.order_id.partner_id.id),('product_tmpl_id','=',rec.product_id.id),('limit_receiving_quantity','=',True),('min_qty','=',min_qty)])
                        limit = round(((rec.product_qty * limit_per.limit_per) / 100) + rec.product_qty)
                        rec.max_limit_received_qty = limit
                if min_min_qty:
                    min_qty1 = float(min(min_min_qty))
                    if rec.product_qty <= min_qty1:
                        limit_per1 = self.env['product.supplierinfo'].search([('name','=',rec.order_id.partner_id.id),('product_tmpl_id','=',rec.product_id.id),('limit_receiving_quantity','=',True),('min_qty','=',min_qty1)])
                        limit1 = round(((rec.product_qty * limit_per1.limit_per) / 100) + rec.product_qty)
                        rec.max_limit_received_qty = limit1
            else:
                rec.max_limit_received_qty = rec.max_limit - rec.qty_received  
                

