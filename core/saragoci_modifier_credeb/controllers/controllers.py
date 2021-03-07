# -*- coding: utf-8 -*-
from odoo import http

# class SaragociModifierCredeb(http.Controller):
#     @http.route('/saragoci_modifier_credeb/saragoci_modifier_credeb/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/saragoci_modifier_credeb/saragoci_modifier_credeb/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('saragoci_modifier_credeb.listing', {
#             'root': '/saragoci_modifier_credeb/saragoci_modifier_credeb',
#             'objects': http.request.env['saragoci_modifier_credeb.saragoci_modifier_credeb'].search([]),
#         })

#     @http.route('/saragoci_modifier_credeb/saragoci_modifier_credeb/objects/<model("saragoci_modifier_credeb.saragoci_modifier_credeb"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('saragoci_modifier_credeb.object', {
#             'object': obj
#         })