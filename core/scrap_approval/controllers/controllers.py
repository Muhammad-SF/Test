# -*- coding: utf-8 -*-
from odoo import http

# class ScrapApproval(http.Controller):
#     @http.route('/scrap_approval/scrap_approval/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/scrap_approval/scrap_approval/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('scrap_approval.listing', {
#             'root': '/scrap_approval/scrap_approval',
#             'objects': http.request.env['scrap_approval.scrap_approval'].search([]),
#         })

#     @http.route('/scrap_approval/scrap_approval/objects/<model("scrap_approval.scrap_approval"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('scrap_approval.object', {
#             'object': obj
#         })