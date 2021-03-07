# -*- coding: utf-8 -*-
from odoo import http

# class ScrapAccounting(http.Controller):
#     @http.route('/scrap_accounting/scrap_accounting/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/scrap_accounting/scrap_accounting/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('scrap_accounting.listing', {
#             'root': '/scrap_accounting/scrap_accounting',
#             'objects': http.request.env['scrap_accounting.scrap_accounting'].search([]),
#         })

#     @http.route('/scrap_accounting/scrap_accounting/objects/<model("scrap_accounting.scrap_accounting"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('scrap_accounting.object', {
#             'object': obj
#         })