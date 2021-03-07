# -*- coding: utf-8 -*-
from odoo import http

# class VendorPaymentStd(http.Controller):
#     @http.route('/vendor_payment_std/vendor_payment_std/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vendor_payment_std/vendor_payment_std/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vendor_payment_std.listing', {
#             'root': '/vendor_payment_std/vendor_payment_std',
#             'objects': http.request.env['vendor_payment_std.vendor_payment_std'].search([]),
#         })

#     @http.route('/vendor_payment_std/vendor_payment_std/objects/<model("vendor_payment_std.vendor_payment_std"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vendor_payment_std.object', {
#             'object': obj
#         })