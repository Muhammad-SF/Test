# -*- coding: utf-8 -*-
from odoo import http

# class SarangociModifierPurchaseRequestLine(http.Controller):
#     @http.route('/sarangoci_modifier_purchase_request_line/sarangoci_modifier_purchase_request_line/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sarangoci_modifier_purchase_request_line/sarangoci_modifier_purchase_request_line/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sarangoci_modifier_purchase_request_line.listing', {
#             'root': '/sarangoci_modifier_purchase_request_line/sarangoci_modifier_purchase_request_line',
#             'objects': http.request.env['sarangoci_modifier_purchase_request_line.sarangoci_modifier_purchase_request_line'].search([]),
#         })

#     @http.route('/sarangoci_modifier_purchase_request_line/sarangoci_modifier_purchase_request_line/objects/<model("sarangoci_modifier_purchase_request_line.sarangoci_modifier_purchase_request_line"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sarangoci_modifier_purchase_request_line.object', {
#             'object': obj
#         })