# -*- coding: utf-8 -*-
from odoo import http

# class SarangociModifierPurchaseOrderLine(http.Controller):
#     @http.route('/sarangoci_modifier_purchase_order_line/sarangoci_modifier_purchase_order_line/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sarangoci_modifier_purchase_order_line/sarangoci_modifier_purchase_order_line/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sarangoci_modifier_purchase_order_line.listing', {
#             'root': '/sarangoci_modifier_purchase_order_line/sarangoci_modifier_purchase_order_line',
#             'objects': http.request.env['sarangoci_modifier_purchase_order_line.sarangoci_modifier_purchase_order_line'].search([]),
#         })

#     @http.route('/sarangoci_modifier_purchase_order_line/sarangoci_modifier_purchase_order_line/objects/<model("sarangoci_modifier_purchase_order_line.sarangoci_modifier_purchase_order_line"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sarangoci_modifier_purchase_order_line.object', {
#             'object': obj
#         })