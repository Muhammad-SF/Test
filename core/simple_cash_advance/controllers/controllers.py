# -*- coding: utf-8 -*-
from odoo import http

# class SimpleCashAdvance(http.Controller):
#     @http.route('/simple_cash_advance/simple_cash_advance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/simple_cash_advance/simple_cash_advance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('simple_cash_advance.listing', {
#             'root': '/simple_cash_advance/simple_cash_advance',
#             'objects': http.request.env['simple_cash_advance.simple_cash_advance'].search([]),
#         })

#     @http.route('/simple_cash_advance/simple_cash_advance/objects/<model("simple_cash_advance.simple_cash_advance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('simple_cash_advance.object', {
#             'object': obj
#         })