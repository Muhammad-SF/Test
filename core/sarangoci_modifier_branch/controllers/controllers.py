# -*- coding: utf-8 -*-
from odoo import http

# class SarangociModifierBranch(http.Controller):
#     @http.route('/sarangoci_modifier_branch/sarangoci_modifier_branch/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sarangoci_modifier_branch/sarangoci_modifier_branch/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sarangoci_modifier_branch.listing', {
#             'root': '/sarangoci_modifier_branch/sarangoci_modifier_branch',
#             'objects': http.request.env['sarangoci_modifier_branch.sarangoci_modifier_branch'].search([]),
#         })

#     @http.route('/sarangoci_modifier_branch/sarangoci_modifier_branch/objects/<model("sarangoci_modifier_branch.sarangoci_modifier_branch"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sarangoci_modifier_branch.object', {
#             'object': obj
#         })