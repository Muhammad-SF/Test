# -*- coding: utf-8 -*-
from odoo import http

# class StdPurchaseAccessRights(http.Controller):
#     @http.route('/std_purchase_access_rights/std_purchase_access_rights/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/std_purchase_access_rights/std_purchase_access_rights/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('std_purchase_access_rights.listing', {
#             'root': '/std_purchase_access_rights/std_purchase_access_rights',
#             'objects': http.request.env['std_purchase_access_rights.std_purchase_access_rights'].search([]),
#         })

#     @http.route('/std_purchase_access_rights/std_purchase_access_rights/objects/<model("std_purchase_access_rights.std_purchase_access_rights"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('std_purchase_access_rights.object', {
#             'object': obj
#         })