# -*- coding: utf-8 -*-
from odoo import http

# class WorkCenterBasedAsset(http.Controller):
#     @http.route('/work_center_based_asset/work_center_based_asset/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/work_center_based_asset/work_center_based_asset/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('work_center_based_asset.listing', {
#             'root': '/work_center_based_asset/work_center_based_asset',
#             'objects': http.request.env['work_center_based_asset.work_center_based_asset'].search([]),
#         })

#     @http.route('/work_center_based_asset/work_center_based_asset/objects/<model("work_center_based_asset.work_center_based_asset"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('work_center_based_asset.object', {
#             'object': obj
#         })