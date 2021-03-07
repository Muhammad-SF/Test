# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class sarangoci_modifier_purchase_order_line(models.Model):
#     _name = 'sarangoci_modifier_purchase_order_line.sarangoci_modifier_purchase_order_line'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    purchase_request = fields.Char(compute='_compute_purchase_request', string="Purchase request")
    supplier = fields.Char(compute='_compute_supplier', string="Supplier")
    purchased_qty = fields.Char(compute='_compute_purchased_qty', string="Quantity in RFQ/PO")
    # name = fields.Char(related='company_id.name', readonly=True)
    unit_price_billed = fields.Char(compute='_compute_unit_price_billed', string="Unit price Billed")
    sub_total_billed = fields.Char(compute='_compute_sub_total_billed', string="Sub Total Billed")


    def _compute_purchase_request(self):
        for purchase_order_line in self:
            if purchase_order_line.purchase_request_lines:
                arrayname = []
                for purchase_request_line in purchase_order_line.purchase_request_lines:
                    arrayname.append(purchase_request_line.request_id.name)
                purchase_order_line.purchase_request = ' ,'.join(arrayname)

    def _compute_supplier(self):
        for purchase_order_line in self:
            if purchase_order_line.purchase_request_lines:
                arrayname = []
                for purchase_request_line in purchase_order_line.purchase_request_lines:
                    if purchase_request_line.supplier_id.name:
                        arrayname.append(purchase_request_line.supplier_id.name)
                purchase_order_line.supplier = ' ,'.join(arrayname)

    def _compute_purchased_qty(self):
        for purchase_order_line in self:
            if purchase_order_line.purchase_request_lines:
                purchased_qty = 0
                for purchase_request_line in purchase_order_line.purchase_request_lines:
                    purchased_qty += purchase_request_line.purchased_qty
                purchase_order_line.purchased_qty = purchased_qty

    def _compute_unit_price_billed(self):
        for purchase_order_line in self:
            if purchase_order_line.invoice_lines:
                unit_price_billed = 0
                for invoice_line in purchase_order_line.invoice_lines:
                    unit_price_billed += invoice_line.price_unit
                purchase_order_line.unit_price_billed = unit_price_billed

    def _compute_sub_total_billed(self):
        for purchase_order_line in self:
            if purchase_order_line.invoice_lines:
                sub_total_billed = 0
                for invoice_line in purchase_order_line.invoice_lines:
                    sub_total_billed += invoice_line.price_unit
                purchase_order_line.sub_total_billed = sub_total_billed