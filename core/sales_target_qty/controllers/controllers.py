# -*- coding: utf-8 -*-
from odoo import http

# class HmSalesStandardization(http.Controller):
#     @http.route('/hm_sales_standardization/hm_sales_standardization/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hm_sales_standardization/hm_sales_standardization/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hm_sales_standardization.listing', {
#             'root': '/hm_sales_standardization/hm_sales_standardization',
#             'objects': http.request.env['hm_sales_standardization.hm_sales_standardization'].search([]),
#         })

#     @http.route('/hm_sales_standardization/hm_sales_standardization/objects/<model("hm_sales_standardization.hm_sales_standardization"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hm_sales_standardization.object', {
#             'object': obj
#         })