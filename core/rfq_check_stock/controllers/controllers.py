# -*- coding: utf-8 -*-
from odoo import http

# class WorkDiary(http.Controller):
#     @http.route('/work_diary/work_diary/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/work_diary/work_diary/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('work_diary.listing', {
#             'root': '/work_diary/work_diary',
#             'objects': http.request.env['work_diary.work_diary'].search([]),
#         })

#     @http.route('/work_diary/work_diary/objects/<model("work_diary.work_diary"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('work_diary.object', {
#             'object': obj
#         })