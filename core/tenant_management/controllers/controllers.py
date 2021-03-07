# -*- coding: utf-8 -*-
from odoo import http

# class TenantManagement(http.Controller):
#     @http.route('/tenant_management/tenant_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tenant_management/tenant_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('tenant_management.listing', {
#             'root': '/tenant_management/tenant_management',
#             'objects': http.request.env['tenant_management.tenant_management'].search([]),
#         })

#     @http.route('/tenant_management/tenant_management/objects/<model("tenant_management.tenant_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tenant_management.object', {
#             'object': obj
#         })