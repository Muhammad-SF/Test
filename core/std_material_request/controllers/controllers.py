# -*- coding: utf-8 -*-
from odoo import http

# class StdMaterialRequest(http.Controller):
#     @http.route('/std_material_request/std_material_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/std_material_request/std_material_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('std_material_request.listing', {
#             'root': '/std_material_request/std_material_request',
#             'objects': http.request.env['std_material_request.std_material_request'].search([]),
#         })

#     @http.route('/std_material_request/std_material_request/objects/<model("std_material_request.std_material_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('std_material_request.object', {
#             'object': obj
#         })