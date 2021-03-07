# -*- coding: utf-8 -*-
from odoo import http

# class WorkingSchedule(http.Controller):
#     @http.route('/working_schedule/working_schedule/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/working_schedule/working_schedule/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('working_schedule.listing', {
#             'root': '/working_schedule/working_schedule',
#             'objects': http.request.env['working_schedule.working_schedule'].search([]),
#         })

#     @http.route('/working_schedule/working_schedule/objects/<model("working_schedule.working_schedule"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('working_schedule.object', {
#             'object': obj
#         })